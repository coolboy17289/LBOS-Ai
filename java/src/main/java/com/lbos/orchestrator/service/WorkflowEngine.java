package com.lbos.orchestrator.service;

import com.lbos.orchestrator.model.Workflow;
import com.lbos.orchestrator.model.WorkflowStep;
import com.lbos.orchestrator.repository.WorkflowRepository;
import com.lbos.orchestrator.repository.WorkflowStepRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.List;

@Service
@RequiredArgsConstructor
@Slf4j
public class WorkflowEngine {

    private final WorkflowRepository workflowRepository;
    private final WorkflowStepRepository stepRepository;
    private final ServiceInvocationService serviceInvocationService;

    /**
     * Execute a workflow
     */
    @Transactional
    public void executeWorkflow(String workflowId) {
        Workflow workflow = workflowRepository.findByWorkflowId(workflowId)
                .orElseThrow(() -> new IllegalArgumentException("Workflow not found: " + workflowId));

        workflow.setStatus(Workflow.WorkflowStatus.RUNNING);
        workflow.setUpdatedAt(Instant.now());
        workflowRepository.save(workflow);

        log.info("Starting workflow execution: {}", workflowId);

        try {
            for (String stepId : workflow.getStepOrder()) {
                WorkflowStep step = stepRepository.findByStepId(stepId)
                        .orElseThrow(() -> new IllegalStateException("Step not found: " + stepId));

                executeStep(workflow, step);
            }

            workflow.setStatus(Workflow.WorkflowStatus.COMPLETED);
            workflow.setUpdatedAt(Instant.now());
            workflowRepository.save(workflow);
            log.info("Workflow completed successfully: {}", workflowId);
        } catch (Exception e) {
            workflow.setStatus(Workflow.WorkflowStatus.FAILED);
            workflow.setUpdatedAt(Instant.now());
            workflowRepository.save(workflow);
            log.error("Workflow execution failed: {}", workflowId, e);
            throw e;
        }
    }

    /**
     * Execute a single step
     */
    private void executeStep(Workflow workflow, WorkflowStep step) {
        step.setStatus(WorkflowStep.StepStatus.RUNNING);
        step.setRetryCount(0);
        step.setUpdatedAt(Instant.now());
        stepRepository.save(step);

        log.info("Executing step: {} ({})", step.getStepName(), step.getStepId());

        try {
            // Invoke the appropriate service based on step configuration
            Object result = serviceInvocationService.invokeService(step);

            // Update step with output
            step.setOutputData(result.toString());
            step.setStatus(WorkflowStep.StepStatus.COMPLETED);
            step.setUpdatedAt(Instant.now());
            stepRepository.save(step);

            log.info("Step completed: {}", step.getStepId());
        } catch (Exception e) {
            handleStepFailure(step, e);
            throw e; // Propagate to workflow level
        }
    }

    /**
     * Handle step failure with retry logic
     */
    private void handleStepFailure(WorkflowStep step, Exception e) {
        step.setRetryCount(step.getRetryCount() + 1);
        step.setLastError(e.getMessage());
        step.setUpdatedAt(Instant.now());

        if (step.getRetryCount() < step.getMaxRetries()) {
            step.setStatus(WorkflowStep.StepStatus.RETRYING);
            stepRepository.save(step);
            log.warn("Step failed, retrying ({}/{}): {}", step.getStepId(), step.getRetryCount(), step.getMaxRetries(), e.getMessage());
            // In a real system, you would schedule a retry after a delay
            // For simplicity, we just retry immediately (could cause stack overflow)
            // Better to use a retry mechanism with delay, but we keep it simple for demo
            try {
                Thread.sleep(1000); // Wait 1 second before retry
                executeStep(null, step); // This is simplified - actual implementation would be async
            } catch (InterruptedException ex) {
                Thread.currentThread().interrupt();
                throw new RuntimeException(ex);
            }
        } else {
            step.setStatus(WorkflowStep.StepStatus.FAILED);
            stepRepository.save(step);
            log.error("Step failed after max retries: {}", step.getStepId(), e);
        }
    }
}