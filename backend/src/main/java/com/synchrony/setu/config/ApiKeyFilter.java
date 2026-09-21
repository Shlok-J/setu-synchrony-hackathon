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
 * Simple shared-key auth: every request except /api/health needs a
 * matching X-API-Key header, but only if app.api-key is actually set.
 * Left opt-in so it doesn't break local testing where no key is set.
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
