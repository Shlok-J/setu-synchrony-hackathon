package com.synchrony.setu.controller;

import java.util.Map;

import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestClient;

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
    public Map<String, Object> score(@RequestBody Map<String, Object> applicantPayload) {
        // Thin-slice: forward straight to the Python model-service.
        // TODO: persist applicant + score history in Postgres (see db/init.sql)
        // once the DB layer is wired up.
        return modelServiceClient.post()
                .uri("/score")
                .contentType(MediaType.APPLICATION_JSON)
                .body(applicantPayload)
                .retrieve()
                .body(Map.class);
    }
}
