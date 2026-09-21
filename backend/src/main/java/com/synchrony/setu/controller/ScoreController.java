package com.synchrony.setu.controller;

import java.util.List;
import java.util.Map;

import jakarta.validation.Valid;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import com.synchrony.setu.dto.ApplicantScoreRequest;
import com.synchrony.setu.service.ApplicantStore;

@RestController
@RequestMapping("/api")
public class ScoreController {

    private final RestClient modelServiceClient;
    private final ApplicantStore applicantStore;

    public ScoreController(RestClient modelServiceClient, ApplicantStore applicantStore) {
        this.modelServiceClient = modelServiceClient;
        this.applicantStore = applicantStore;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "service", "setu-backend");
    }

    /**
     * Consent must be recorded before /score will run for a given applicant.
     * Placeholder for the `applicants.consent_given` column in db/init.sql --
     * see ApplicantStore.
     */
    @PostMapping("/consent")
    public Map<String, Object> giveConsent(@RequestBody Map<String, Object> body) {
        String applicantId = String.valueOf(body.get("applicant_id"));
        boolean given = Boolean.TRUE.equals(body.get("consent_given"));
        applicantStore.setConsent(applicantId, given);
        return Map.of("applicant_id", applicantId, "consent_given", given);
    }

    @PostMapping("/score")
    public ResponseEntity<?> score(@Valid @RequestBody ApplicantScoreRequest request) {
        if (!applicantStore.hasConsent(request.applicant_id())) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN).body(Map.of(
                    "error", "consent required",
                    "message", "Call POST /api/consent for this applicant_id before requesting a score."
            ));
        }

        // Forward straight to the Python model-service, which owns the ML.
        try {
            Map<?, ?> body = modelServiceClient.post()
                    .uri("/score")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(Map.class);
            applicantStore.recordScore(request.applicant_id(), (Map<String, Object>) body);
            return ResponseEntity.ok(body);
        } catch (RestClientException e) {
            // Debug aid: surface the real cause instead of a bare 500 so a
            // failure is diagnosable from the browser alone. Tighten/remove
            // before anything resembling a production submission.
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(Map.of(
                    "error", "model-service call failed",
                    "exceptionType", e.getClass().getName(),
                    "message", String.valueOf(e.getMessage())
            ));
        }
    }

    /** Shows the same applicant's score sharpening over time (see DESIGN.md section 2). */
    @GetMapping("/applicants/{id}/history")
    public List<Map<String, Object>> history(@PathVariable("id") String id) {
        return applicantStore.getHistory(id);
    }

    /** Right-to-erasure (DPDP Act 2023) as an actual endpoint, not just a policy statement. */
    @DeleteMapping("/applicants/{id}")
    public Map<String, Object> forgetApplicant(@PathVariable("id") String id) {
        applicantStore.forget(id);
        return Map.of("applicant_id", id, "status", "erased");
    }

    @GetMapping("/fairness-report")
    public ResponseEntity<?> fairnessReport() {
        try {
            Map<?, ?> body = modelServiceClient.get()
                    .uri("/fairness-report")
                    .retrieve()
                    .body(Map.class);
            return ResponseEntity.ok(body);
        } catch (RestClientException e) {
            return ResponseEntity.status(HttpStatus.BAD_GATEWAY).body(Map.of(
                    "error", "model-service call failed",
                    "exceptionType", e.getClass().getName(),
                    "message", String.valueOf(e.getMessage())
            ));
        }
    }
}
