package com.lbos.orchestrator.service;

import com.lbos.orchestrator.controller.WorkflowController;
import com.lbos.orchestrator.model.Workflow;
import com.lbos.orchestrator.model.WorkflowStep;
import com.lbos.orchestrator.repository.WorkflowRepository;
import com.lbos.orchestrator.repository.WorkflowStepRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Service
@RequiredArgsConstructor
@Slf4j
public class WorkflowEngineService {

    private final WorkflowRepository workflowRepository;
    private final WorkflowStepRepository workflowStepRepository;
    private final RestTemplate restTemplate = new RestTemplate();

    /**
     * Execute a workflow by sequentially running its steps
     */
    public void executeWorkflow(String workflowId) {
        log.info("Starting execution of workflow: {}", workflowId);

        // Load workflow
        Optional<Workflow> workflowOpt = workflowRepository.findByWorkflowId(workflowId);
        if (workflowOpt.isEmpty()) {
            throw new IllegalArgumentException("Workflow not found: " + workflowId);
        }
        Workflow workflow = workflowOpt.get();

        // Update workflow status to RUNNING
        workflow.setStatus(Workflow.WorkflowStatus.RUNNING);
        workflow.setUpdatedAt(Instant.now());
        workflowRepository.save(workflow);

        try {
            // Get ordered steps
            List<WorkflowStep> steps = new ArrayList<>();
            for (String stepId : workflow.getStepOrder()) {
                workflowStepRepository.findByStepId(stepId)
                        .ifPresent(steps::add);
            }

            // Execute each step in order
            for (WorkflowStep step : steps) {
                executeStep(step);
            }

            // Mark workflow as completed
            workflow.setStatus(Workflow.WorkflowStatus.COMPLETED);
            workflow.setUpdatedAt(Instant.now());
            workflowRepository.save(workflow);
            log.info("Workflow completed: {}", workflowId);
        } catch (Exception e) {
            // Mark workflow as failed
            workflow.setStatus(Workflow.WorkflowStatus.FAILED);
            workflow.setUpdatedAt(Instant.now());
            workflowRepository.save(workflow);
            log.error("Workflow execution failed: {}", workflowId, e);
            throw e;
        }
    }

    /**
     * Execute a single step by calling the appropriate service
     */
    private void executeStep(WorkflowStep step) {
        log.info("Executing step: {} ({})", step.getStepName(), step.getStepId());

        // Update step status to RUNNING
        step.setStatus(WorkflowStep.StepStatus.RUNNING);
        step.setUpdatedAt(Instant.now());
        workflowStepRepository.save(step);

        try {
            // Based on service type, call appropriate endpoint
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            HttpEntity<String> request = new HttpEntity<>(step.getInputData(), headers);

            ResponseEntity<String> response;
            switch (step.getServiceType()) {
                case "INGESTION":
                    response = restTemplate.exchange(
                            step.getServiceEndpoint(),
                            HttpMethod.POST,
                            request,
                            String.class
                    );
                    break;
                case "TRAINING":
                    response = restTemplate.exchange(
                            step.getServiceEndpoint(),
                            HttpMethod.POST,
                            request,
                            String.class
                    );
                    break;
                case "EVALUATION":
                    response = restTemplate.exchange(
                            step.getServiceEndpoint(),
                            HttpMethod.POST,
                            request,
                            String.class
                    );
                    break;
                default:
                    throw new IllegalArgumentException("Unknown service type: " + step.getServiceType());
            }

            // Update step with output
            step.setOutputData(response.getBody());
            step.setStatus(WorkflowStep.StepStatus.COMPLETED);
            step.setRetryCount(0); // Reset retry count on success
            step.setUpdatedAt(Instant.now());
            workflowStepRepository.save(step);
            log.info("Step completed: {}", step.getStepName());
        } catch (Exception ex) {
            // Handle failure
            int retryCount = step.getRetryCount() + 1;
            step.setRetryCount(retryCount);
            step.setLastError(ex.getMessage());

            if (step.getRetryCount() < step.getMaxRetries()) {
                step.setStatus(WorkflowStep.StepStatus.RETRYING);
                step.setUpdatedAt(Instant.now());
                workflowStepRepository.save(step);
                log.warn("Step failed, retrying ({}/{}): {}", step.getRetryCount(), step.getMaxRetries(), step.getStepName());
                // In a real system, we would retry after a delay or via a message queue
                // For simplicity, we'll just retry immediately (but this could cause infinite loops)
                // Better approach would be to use a scheduler or message queue with delay
                executeStep(step); // Recursive retry (not ideal for production)
            } else {
                step.setStatus(WorkflowStep.StepStatus.FAILED);
                step.setUpdatedAt(Instant.now());
                workflowStepRepository.save(step);
                log.error("Step failed after max retries: {}", step.getStepName(), ex);
                throw new RuntimeException("Step failed after max retries: " + step.getStepName(), ex);
            }
        }
    }
}