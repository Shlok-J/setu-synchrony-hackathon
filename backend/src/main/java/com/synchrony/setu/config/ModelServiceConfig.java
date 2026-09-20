package com.synchrony.setu.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

@Configuration
public class ModelServiceConfig {

    @Value("${model.service.base-url:http://localhost:8000}")
    private String modelServiceBaseUrl;

    @Bean
    public RestClient modelServiceClient() {
        // The default (JDK HttpClient-backed) request factory streams the
        // request body using chunked transfer-encoding, whose framing
        // uvicorn/h11 on the model-service side was failing to parse,
        // resulting in an apparently empty body. These payloads are small
        // (a few hundred bytes), so buffer them and send a real
        // Content-Length instead of streaming/chunking.
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setOutputStreaming(false);

        return RestClient.builder()
                .baseUrl(modelServiceBaseUrl)
                .requestFactory(factory)
                .build();
    }
}
