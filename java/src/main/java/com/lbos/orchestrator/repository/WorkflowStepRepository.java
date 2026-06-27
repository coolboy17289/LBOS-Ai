package com.lbos.orchestrator.repository;

import com.lbos.orchestrator.model.WorkflowStep;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface WorkflowStepRepository extends JpaRepository<WorkflowStep, Long> {
    Optional<WorkflowStep> findByStepId(String stepId);
    List<WorkflowStep> findByWorkflowIdOrderById(String workflowId);
}