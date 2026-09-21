package com.synchrony.setu.service;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import org.springframework.stereotype.Component;

/**
 * In-memory placeholder for the `applicants` / `score_history` tables
 * defined in db/init.sql. Real Postgres persistence is designed (see
 * DESIGN.md) but not yet wired up -- this gives the consent, score-history,
 * and right-to-erasure behavior real enforcement now without betting more
 * time on an untested Java+JDBC+Docker integration under a deadline.
 * Swap this class's internals for a Postgres-backed repository later; the
 * method signatures below are what a real repository would also expose.
 */
@Component
public class ApplicantStore {

    private final Map<String, Boolean> consent = new ConcurrentHashMap<>();
    private final Map<String, List<Map<String, Object>>> scoreHistory = new ConcurrentHashMap<>();

    public void setConsent(String applicantId, boolean given) {
        consent.put(applicantId, given);
    }

    public boolean hasConsent(String applicantId) {
        return consent.getOrDefault(applicantId, false);
    }

    public void recordScore(String applicantId, Map<String, Object> scoreResult) {
        scoreHistory
                .computeIfAbsent(applicantId, key -> Collections.synchronizedList(new ArrayList<>()))
                .add(scoreResult);
    }

    public List<Map<String, Object>> getHistory(String applicantId) {
        return scoreHistory.getOrDefault(applicantId, List.of());
    }

    /** Right-to-erasure: forgets everything about this applicant. */
    public void forget(String applicantId) {
        consent.remove(applicantId);
        scoreHistory.remove(applicantId);
    }
}
