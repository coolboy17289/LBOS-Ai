package com.lbos.orchestrator.repository;

import com.lbos.orchestrator.model.Workflow;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface WorkflowRepository extends JpaRepository<Workflow, String> {
    Optional<Workflow> findByWorkflowId(String workflowId);
}