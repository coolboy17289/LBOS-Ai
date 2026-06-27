package com.lbos.orchestrator.controller;

import com.lbos.orchestrator.service.WorkflowEngineService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/workflows")
@RequiredArgsConstructor
@Slf4j
public class WorkflowController {

    private final WorkflowEngineService workflowEngineService;

    /**
     * Execute a workflow by ID
     */
    @PostMapping("/{workflowId}/execute")
    public ResponseEntity<?> executeWorkflow(@PathVariable String workflowId) {
        try {
            // This runs synchronously; in production, you'd use async or message queue
            workflowEngineService.executeWorkflow(workflowId);
            return ResponseEntity.ok().body("Workflow execution started: " + workflowId);
        } catch (Exception e) {
            log.error("Failed to execute workflow {}", workflowId, e);
            return ResponseEntity.badRequest().body("Failed to execute workflow: " + e.getMessage());
        }
    }

    /**
     * Get workflow status (placeholder)
     */
    @GetMapping("/{workflowId}/status")
    public ResponseEntity<?> getWorkflowStatus(@PathVariable String workflowId) {
        // TODO: Implement using workflow repository
        return ResponseEntity.ok().body("Status for workflow: " + workflowId + " (not fully implemented)");
    }

    /**
     * Create a simple demo workflow for ingestion -> training -> evaluation
     * This is just for demonstration; in a real system, workflows would be defined via API or config
     */
    @PostMapping("/create-demo")
    public ResponseEntity<?> createDemoWorkflow() {
        // TODO: Implement workflow creation using repositories
        return ResponseEntity.ok().body("Demo workflow creation endpoint (not implemented)");
    }
}