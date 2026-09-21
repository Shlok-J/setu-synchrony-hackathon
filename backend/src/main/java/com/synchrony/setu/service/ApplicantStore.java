package com.synchrony.setu.service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Component;

/**
 * Real Postgres-backed persistence for consent, score history, and
 * right-to-erasure, against the schema in db/init.sql. Score results are
 * stored as a JSON text column (`result_json`) rather than a fully
 * normalized schema for `top_factors` -- simplest correct option given the
 * time available, and Jackson is already on the classpath via
 * spring-boot-starter-web.
 *
 * Method signatures are unchanged from the in-memory version this replaces,
 * so ScoreController needed no changes at all -- exactly the point of
 * keeping this behind its own class from the start.
 */
@Component
public class ApplicantStore {

    private final JdbcTemplate jdbc;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public ApplicantStore(JdbcTemplate jdbc) {
        this.jdbc = jdbc;
    }

    public void setConsent(String applicantId, boolean given) {
        jdbc.update(
                "INSERT INTO applicants (applicant_id, consent_given) VALUES (?, ?) "
                        + "ON CONFLICT (applicant_id) DO UPDATE SET consent_given = EXCLUDED.consent_given",
                applicantId, given
        );
    }

    public boolean hasConsent(String applicantId) {
        List<Boolean> rows = jdbc.query(
                "SELECT consent_given FROM applicants WHERE applicant_id = ?",
                (rs, rowNum) -> rs.getBoolean("consent_given"),
                applicantId
        );
        return !rows.isEmpty() && rows.get(0);
    }

    public void recordScore(String applicantId, Map<String, Object> scoreResult) {
        if (scoreResult == null) {
            return;
        }
        try {
            String json = objectMapper.writeValueAsString(scoreResult);
            Object riskScore = scoreResult.get("risk_score");
            jdbc.update(
                    "INSERT INTO score_history (applicant_id, risk_score, method, explanation, result_json) "
                            + "VALUES (?, ?, ?, ?, ?)",
                    applicantId,
                    riskScore == null ? null : Double.valueOf(riskScore.toString()),
                    stringOrNull(scoreResult.get("method")),
                    stringOrNull(scoreResult.get("explanation")),
                    json
            );
        } catch (Exception e) {
            // Best-effort logging: a persistence hiccup should never break the
            // score response the applicant is actually waiting on.
        }
    }

    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> getHistory(String applicantId) {
        List<String> jsonRows = jdbc.query(
                "SELECT result_json FROM score_history WHERE applicant_id = ? ORDER BY scored_at",
                (rs, rowNum) -> rs.getString("result_json"),
                applicantId
        );
        List<Map<String, Object>> results = new ArrayList<>();
        for (String json : jsonRows) {
            if (json == null) {
                continue;
            }
            try {
                results.add(objectMapper.readValue(json, Map.class));
            } catch (Exception e) {
                // skip a malformed row rather than fail the whole history read
            }
        }
        return results;
    }

    /** Right-to-erasure (DPDP Act 2023) as a real delete, not just an in-memory clear. */
    public void forget(String applicantId) {
        jdbc.update("DELETE FROM score_history WHERE applicant_id = ?", applicantId);
        jdbc.update("DELETE FROM applicants WHERE applicant_id = ?", applicantId);
    }

    private static String stringOrNull(Object o) {
        return o == null ? null : o.toString();
    }
}
