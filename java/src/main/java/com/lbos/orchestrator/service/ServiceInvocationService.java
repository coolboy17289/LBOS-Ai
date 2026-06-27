package com.lbos.orchestrator.service;

import com.lbos.orchestrator.model.WorkflowStep;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Service
@RequiredArgsConstructor
@Slf4j
public class ServiceInvocationService {

    private final RestTemplate restTemplate;

    // Base URLs for services (could be configured via properties)
    private static final String INGESTION_SERVICE_URL = "http://localhost:5000/api/ingest";
    private static final String TRAINING_SERVICE_URL = "http://localhost:5001/api/train";
    private static final String EVALUATION_SERVICE_URL = "http://localhost:5002/api/evaluate";

    /**
     * Invoke the appropriate service based on step configuration
     */
    public Object invokeService(WorkflowStep step) {
        String serviceType = step.getServiceType();
        String endpoint = step.getServiceEndpoint();
        String inputJson = step.getInputData();

        log.info("Invoking service: {} at {}", serviceType, endpoint);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<String> request = new HttpEntity<>(inputJson, headers);

        ResponseEntity<String> response;
        try {
            response = restTemplate.exchange(
                    endpoint,
                    HttpMethod.POST,
                    request,
                    String.class
            );
        } catch (Exception e) {
            throw new RuntimeException("Failed to invoke service " + serviceType + ": " + e.getMessage(), e);
        }

        if (response.getStatusCode().is2xxSuccessful()) {
            log.info("Service call successful: {}", response.getBody());
            return response.getBody();
        } else {
            throw new RuntimeException("Service call failed with status: " + response.getStatusCode());
        }
    }

    // Convenience methods for specific service types (optional)
    public String invokeIngestionService(String inputJson) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<String> request = new HttpEntity<>(inputJson, headers);

        ResponseEntity<String> response = restTemplate.exchange(
                INGESTION_SERVICE_URL,
                HttpMethod.POST,
                request,
                String.class
        );

        if (response.getStatusCode().is2xxSuccessful()) {
            return response.getBody();
        } else {
            throw new RuntimeException("Ingestion service failed: " + response.getStatusCode());
        }
    }

    public String invokeTrainingService(String inputJson) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<String> request = new HttpEntity<>(inputJson, headers);

        ResponseEntity<String> response = restTemplate.exchange(
                TRAINING_SERVICE_URL,
                HttpMethod.POST,
                request,
                String.class
        );

        if (response.getStatusCode().is2xxSuccessful()) {
            return response.getBody();
        } else {
            throw new RuntimeException("Training service failed: " + response.getStatusCode());
        }
    }

    public String invokeEvaluationService(String inputJson) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<String> request = new HttpEntity<>(inputJson, headers);

        ResponseEntity<String> response = restTemplate.exchange(
                EVALUATION_SERVICE_URL,
                HttpMethod.POST,
                request,
                String.class
        );

        if (response.getStatusCode().is2xxSuccessful()) {
            return response.getBody();
        } else {
            throw new RuntimeException("Evaluation service failed: " + response.getStatusCode());
        }
    }
}