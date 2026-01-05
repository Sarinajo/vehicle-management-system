pipeline {
  agent any
  stages {
    stage('Start'){
      steps {
        echo "Pipeline Started && Login successfully "
      }
    }
    stage('Docker Build') {
      steps {
        sh 'docker build -t vehicle_mgmt:latest .'
      }
    }
    stage('Run Docker compose') {
      steps {
        sh 'docker-compose --profile initialize up -d'
      }
    }
  }
}
