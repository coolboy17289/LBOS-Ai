module.exports = (sequelize, DataTypes) => {
  const Evaluation = sequelize.define('Evaluation', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    evaluationId: {
      type: DataTypes.UUID,
      defaultValue: DataTypes.UUIDV4,
      unique: true,
      allowNull: false
    },
    modelId: {
      type: DataTypes.UUID,
      allowNull: false,
      references: {
        model: 'models',
        key: 'modelId'
      }
    },
    testSetId: {
      type: DataTypes.UUID,
      allowNull: false
    },
    metrics: {
      type: DataTypes.TEXT,
      allowNull: true
    },
    status: {
      type: DataTypes.ENUM('queued', 'processing', 'completed', 'failed'),
      defaultValue: 'queued'
    },
    reportUrl: {
      type: DataTypes.STRING(255),
      allowNull: true
    },
    completedAt: {
      type: DataTypes.DATE,
      allowNull: true
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
    tableName: 'evaluations',
    indexes: [
      {
        name: 'idx_eval_model',
        fields: ['modelId']
      },
      {
        name: 'idx_eval_status',
        fields: ['status']
      },
      {
        name: 'idx_eval_created',
        fields: ['createdAt']
      }
    ]
  });

  Evaluation.associate = (models) => {
    Evaluation.belongsTo(models.Model, { foreignKey: 'modelId', as: 'model' });
  };

  return Evaluation;
};