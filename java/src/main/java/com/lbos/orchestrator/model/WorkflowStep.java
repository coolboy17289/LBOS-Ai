package com.lbos.orchestrator.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;

@Entity
@Table(name = "workflow_steps")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class WorkflowStep {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "step_id", length = 36, nullable = false, updatable = false)
    private String stepId;

    @Column(nullable = false)
    private String stepName;

    @Column(name = "workflow_id", nullable = false)
    private String workflowId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private StepStatus status = StepStatus.PENDING;

    @Column(nullable = false)
    private String serviceType;

    @Column(nullable = false)
    private String serviceEndpoint;

    @Column(columnDefinition = "TEXT")
    private String inputData;

    @Column(columnDefinition = "TEXT")
    private String outputData;

    private Integer retryCount = 0;
    private Integer maxRetries = 3;

    @Column(name = "created_at")
    private Instant createdAt = Instant.now();

    @Column(name = "updated_at")
    private Instant updatedAt = Instant.now();

    public enum StepStatus {
        PENDING,
        RUNNING,
        COMPLETED,
        FAILED,
        RETRYING
    }
}