module.exports = (sequelize, DataTypes) => {
  const Log = sequelize.define('Log', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    jobId: {
      type: DataTypes.UUID,
      allowNull: false,
      references: {
        model: 'pipeline_jobs',
        key: 'jobId'
      }
    },
    level: {
      type: DataTypes.ENUM('debug', 'info', 'warn', 'error'),
      defaultValue: 'info'
    },
    message: {
      type: DataTypes.TEXT,
      allowNull: false
    },
    timestamp: {
      type: DataTypes.DATE,
      allowNull: false,
      defaultValue: DataTypes.NOW
    }
  }, {
    tableName: 'logs',
    indexes: [
      {
        name: 'idx_log_job',
        fields: ['jobId']
      },
      {
        name: 'idx_log_level',
        fields: ['level']
      },
      {
        name: 'idx_log_timestamp',
        fields: ['timestamp']
      }
    ]
  });

  Log.associate = (models) => {
    Log.belongsTo(models.PipelineJob, { foreignKey: 'jobId', as: 'job' });
  };

  return Log;
};