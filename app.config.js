const appJson = require('./app.json');

module.exports = ({ config }) => {
  const baseUrl = process.env.EXPO_BASE_PATH;

  return {
    ...config,
    ...appJson.expo,
    experiments: {
      ...config.experiments,
      ...appJson.expo.experiments,
      ...(baseUrl ? { baseUrl } : {}),
    },
    web: {
      ...config.web,
      ...appJson.expo.web,
      output: 'single',
    },
  };
};
