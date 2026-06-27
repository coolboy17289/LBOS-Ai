module.exports = (sequelize, DataTypes) => {
  const User = sequelize.define('User', {
    id: {
      type: DataTypes.INTEGER,
      primaryKey: true,
      autoIncrement: true
    },
    username: {
      type: DataTypes.STRING(50),
      unique: true,
      allowNull: false
    },
    email: {
      type: DataTypes.STRING(100),
      unique: true,
      allowNull: false
    },
    passwordHash: {
      type: DataTypes.STRING(255),
      allowNull: false
    },
    role: {
      type: DataTypes.ENUM('user', 'admin', 'operator'),
      defaultValue: 'user'
    },
    isActive: {
      type: DataTypes.BOOLEAN,
      defaultValue: true
    },
    lastLoginAt: {
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
    tableName: 'users',
    indexes: [
      {
        name: 'idx_user_username',
        fields: ['username']
      },
      {
        name: 'idx_user_email',
        fields: ['email']
      },
      {
        name: 'idx_user_role',
        fields: ['role']
      }
    ]
  });

  User.associate = (models) => {
    User.hasMany(models.Model, { foreignKey: 'createdBy', as: 'createdModels' });
    User.hasMany(models.PipelineJob, { foreignKey: 'createdBy', as: 'createdJobs' });
    User.hasMany(models.Log, { foreignKey: 'createdBy', as: 'createdLogs' });
  };

  return User;
};