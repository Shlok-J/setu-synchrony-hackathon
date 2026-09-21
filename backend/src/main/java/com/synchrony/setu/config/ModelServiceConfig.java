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
        // the default request factory streams the body as chunked, which
        // uvicorn on the other end couldn't parse (arrived as an empty
        // body) -- buffering it and sending a real Content-Length instead
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setOutputStreaming(false);

        return RestClient.builder()
                .baseUrl(modelServiceBaseUrl)
                .requestFactory(factory)
                .build();
    }
}
