package com.synchrony.setu.config;

import java.io.IOException;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

/**
 * Minimal API-key auth: every request except /api/health must carry a
 * matching X-API-Key header, IF an app.api-key is actually configured.
 *
 * "Authentication/authorization basics" per the problem statement's
 * architecture list -- intentionally simple (one shared key, not
 * per-user identity/OAuth2) given the scope of an overnight hackathon
 * build. Left opt-in via APP_API_KEY so it doesn't silently break local
 * dev/Codespace testing that never set one; the live AWS deployment has
 * a real key set, so it's genuinely enforced there.
 */
@Component
public class ApiKeyFilter extends OncePerRequestFilter {

    @Value("${app.api-key:}")
    private String expectedApiKey;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException {

        boolean isHealthCheck = request.getRequestURI().endsWith("/api/health");

        if (isHealthCheck || expectedApiKey == null || expectedApiKey.isBlank()) {
            chain.doFilter(request, response);
            return;
        }

        if (!expectedApiKey.equals(request.getHeader("X-API-Key"))) {
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            response.setContentType("application/json");
            response.getWriter().write("{\"error\":\"missing or invalid X-API-Key header\"}");
            return;
        }

        chain.doFilter(request, response);
    }
}
