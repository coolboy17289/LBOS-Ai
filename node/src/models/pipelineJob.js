module.exports = (sequelize, DataTypes) => {
  const PipelineJob = sequelize.define('PipelineJob', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    jobId: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      unique: true,
      allowNull: false
    },
    type: {
      type: DataTypes.ENUM('ingestion', 'training', 'evaluation'),
      allowNull: false
    },
    status: {
      type: DataTypes.ENUM('queued', 'processing', 'completed', 'failed', 'cancelled'),
      defaultValue: 'queued'
    },
    progress: {
      type: DataTypes.INTEGER,
      defaultValue: 0,
      validate: {
        min: 0,
        max: 100
      }
    },
    inputData: {
      type: DataTypes.TEXT,
      allowNull: true
    },
    result: {
      type: DataTypes.TEXT,
      allowNull: true
    },
    errorMessage: {
      type: DataTypes.TEXT,
      allowNull: true
    },
    modelId: {
      type: DataTypes.UUID,
      allowNull: true,
      references: {
        model: 'models',
        key: 'modelId'
      }
    },
    createdBy: {
      type: DataTypes.INTEGER,
      allowNull: true,
      references: {
        model: 'users',
        key: 'id'
      }
    },
    createdAt: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW
    },
    updatedAt: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW
    }
  }, {
    tableName: 'pipeline_jobs',
    indexes: [
      {
        name: 'idx_job_status',
        fields: ['status']
      },
      {
        name: 'idx_job_type',
        fields: ['type']
      },
      {
        name: 'idx_job_created',
        fields: ['createdAt']
      },
      {
        name: 'idx_job_model',
        fields: ['modelId']
      }
    ]
  });

  PipelineJob.associate = (models) => {
    PipelineJob.belongsTo(models.Model, { foreignKey: 'modelId', as: 'model' });
    PipelineJob.belongsTo(models.User, { foreignKey: 'createdBy', as: 'creator' });
    PipelineJob.hasMany(models.Log, { foreignKey: 'jobId', as: 'logs' });
  };

  return PipelineJob;
};