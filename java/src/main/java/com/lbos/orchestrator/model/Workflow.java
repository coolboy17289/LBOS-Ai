package com.lbos.orchestrator.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Entity
@Table(name = "workflows")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class Workflow {

    @Id
    @Column(name = "workflow_id", length = 36, updatable = false, nullable = false)
    private String workflowId;

    @Column(nullable = false)
    private String workflowName;

    @ElementCollection
    @CollectionTable(name = "workflow_step_order", joinColumns = @JoinColumn(name = "workflow_id"))
    @Column(name = "step_id")
    private List<String> stepOrder = new ArrayList<>();

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private WorkflowStatus status = WorkflowStatus.CREATED;

    @Column(name = "created_at")
    private Instant createdAt = Instant.now();

    @Column(name = "updated_at")
    private Instant updatedAt = Instant.now();

    public enum WorkflowStatus {
        CREATED,
        RUNNING,
        COMPLETED,
        FAILED,
        CANCELLED
    }
}