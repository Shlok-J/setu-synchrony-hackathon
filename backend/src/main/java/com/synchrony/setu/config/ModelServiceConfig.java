package com.synchrony.setu.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestClient;

@Configuration
public class ModelServiceConfig {

    @Value("${model.service.base-url:http://localhost:8000}")
    private String modelServiceBaseUrl;

    @Bean
    public RestClient modelServiceClient() {
        return RestClient.builder().baseUrl(modelServiceBaseUrl).build();
    }
}
