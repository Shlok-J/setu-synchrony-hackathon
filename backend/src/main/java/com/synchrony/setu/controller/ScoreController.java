package com.synchrony.setu.controller;

import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import com.synchrony.setu.dto.ApplicantScoreRequest;

@RestController
@RequestMapping("/api")
public class ScoreController {

    private final RestClient modelServiceClient;

    public ScoreController(RestClient modelServiceClient) {
        this.modelServiceClient = modelServiceClient;
    }

    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of("status", "ok", "service", "setu-backend");
    }

    @PostMapping("/score")
    public ResponseEntity<?> score(@RequestBody ApplicantScoreRequest request) {
        // Thin-slice: forward straight to the Python model-service.
        // TODO: persist applicant + score history in Postgres (see db/init.sql)
        // once the DB layer is wired up.
        try {
            Map<?, ?> body = modelServiceClient.post()
                    .uri("/score")
                    .contentType(MediaType.APPLICATION_JSON)
                    .body(request)
                    .retrieve()
                    .body(Map.class);
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
}
