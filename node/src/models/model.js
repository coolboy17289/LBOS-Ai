module.exports = (sequelize, DataTypes) => {
  const Model = sequelize.define('Model', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    modelId: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      unique: true,
      allowNull: false
    },
    name: {
      type: DataTypes.STRING(100),
      allowNull: false
    },
    version: {
      type: DataTypes.STRING(20),
      defaultValue: '1.0.0'
    },
    status: {
      type: DataTypes.ENUM('training', 'ready', 'archived', 'failed'),
      defaultValue: 'training'
    },
    architecture: {
      type: DataTypes.JSONB,
      allowNull: true
    },
    hyperparameters: {
      type: DataTypes.JSONB,
      allowNull: true
    },
    metrics: {
      type: DataTypes.JSONB,
      allowNull: true
    },
    config: {
      type: DataTypes.TEXT,
      allowNull: true
    },
    filePath: {
      type: DataTypes.STRING(255),
      allowNull: true
    },
    fileSize: {
      type: DataTypes.BIGINT,
      allowNull: true
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
    tableName: 'models',
    indexes: [
      {
        name: 'idx_model_name',
        fields: ['name']
      },
      {
        name: 'idx_model_status',
        fields: ['status']
      },
      {
        name: 'idx_model_created',
        fields: ['createdAt']
      },
      {
        name: 'idx_model_creator',
        fields: ['createdBy']
      }
    ]
  });

  Model.associate = (models) => {
    Model.belongsTo(models.User, { foreignKey: 'createdBy', as: 'creator' });
    Model.hasMany(models.Evaluation, { foreignKey: 'modelId', as: 'evaluations' });
    Model.hasMany(models.PipelineJob, { foreignKey: 'modelId', as: 'jobs' });
  };

  return Model;
};