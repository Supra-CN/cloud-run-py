# Google Cloud Run python 工程实践

## 目标

1. 采用 google cloud run 部署一个简单的 web 服务
2. 采用 google firebase 通过反向代理这个服务，并配合 cloudflare 来实现自定义网域
3. 为什么要采用这种曲折方式来实现自定义网域
   - 因为 google cloud run 他自己的自定义网域功能是 beta 功能，他妈的不好使！
   - 还因为 google compute engine 虚拟机用 nginx 配置反向代理后，也他妈的不好使，访问返回 google 大前端的 404 页面，但是 curl 可以返回正常结果，
   - 还因为尝试了 vpc 等一些其他低成本的方案，仍然他妈不好使。
   - 谁能教教我，我到底错哪儿了

## google firebase 配置笔记

> - **参考：**
>   - [使用 Firebase Hosting 提供动态内容和托管微服务](https://firebase.google.com/docs/hosting/serverless-overview?authuser=0&hl=zh)
>   - [Firebase Hosting](https://firebase.google.com/docs/hosting/?hl=zh&authuser=0&_gl=1*rkvjn*_ga*MTQ0MzI1NzkwMS4xNzQwNTgwNTcy*_ga_CW55HF8NVT*MTc0MDYyNDgzMC4yLjEuMTc0MDYyNTExMi4xNy4wLjA.#implementation_path)
> - **注意：** 
>   - 即使 Cloud Functions 和 Cloud Run 的请求超时时间较长，Firebase Hosting 也受到请求超时时间（60
      秒）限制。如果您的应用需要运行 60 秒以上的时间来处理请求，您会收到 HTTPS 状态代码 504（请求超时）。

<a id="create_gcloud_project"></a>

### 创建并选择你的 google cloud 和 firebase project

### 安装 Firebase CLI

> - **参考：** [Firebase CLI 参考文档](https://firebase.google.com/docs/cli?authuser=0&hl=zh-cn)
    
步骤：
1. 通过 nvm 安装 node.js，参考：[通过 nvm 安装 node.js](#install_nodejs_with_nvm)
2. 安装 Firebase CLI 工具：`npm install -g firebase-tools`
2. Firebase CLI 工具登录：`firebase login`
3. 初始化 Firebase 项目：`firebase init`，参考：[初始化 Firebase Hosting 项目向导](#init_firebase_hosting_project)
4. 配置反向代理重写规则：参考：[将 Hosting 收到的请求定向到您的容器化应用](#rewrites)
5. 部署，`firebase deploy --only hosting:cloud-run-py`
6. 自定义网域，根据平台提示，傻瓜式操作，DNS 添加 CNAME 记录，添加 __acme-challenge DNS 挑战记录

<a id="install_nodejs_with_nvm"></a>

#### 通过 nvm 安装 node.js

> **参考：** [NVM 安装](https://github.com/nvm-sh/nvm/blob/master/README.md)

1. 安装 nvm `$> curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash`
2. 安装node.js合适的版本，双数大版本号为 LTS 版，例如：`nvm install 20`
3. 配置默认版本，参数`-g`为全局配置，例如：`nvm alias default 20`
4. 使用版本特定版本`nvm use 20 `，或默认版本`nvm use default`

<a id="init_firebase_hosting_project"></a>

#### 初始化 Firebase Hosting 项目向导

> **参考：** [NVM 安装](https://github.com/nvm-sh/nvm/blob/master/README.md)

- **步骤1：** `=== Project Setup` 选择合适的项目，回顾：[创建并选择你的 google cloud 和 firebase project](#create_gcloud_project)
- **步骤2：** `=== Hosting Setup` 选择合适的配置
    - **子项1：** `? What do you want to use as your public directory?` 选择产物目录,需配置 git
      ignore，例如：`output/firebase/public`
    - **子项2：** `? Configure as a single-page app (rewrite all urls to /index.html)?` 是否单页应用（SPA）？否（No），仅需反向代理，无需
      rewrite 到首页
    - **子项3：** `? Set up automatic builds and deploys with GitHub?` 自动构建？推荐否（No），推荐手动部署，变动频率低，降低构建复杂度

<a id="rewrites"></a>
#### 将 Hosting 收到的请求定向到您的容器化应用

> - **参考：** 
>   - [使用 Cloud Run 提供动态内容和托管微服务](https://firebase.google.com/docs/hosting/cloud-run?authuser=0&hl=zh-cn)
>   - [配置 Hosting 行为](https://firebase.google.com/docs/hosting/full-config?authuser=0&hl=zh-cn#rewrite-cloud-run-container)

参考下面代码块解释，其中：
1. `serviceId`为 cloud run 服务 id，可在 Cloud Run url 中找到，如：`SERVICE_ID-123456.region.web.app`
2. `pinTag`用于确保请求的正确的静态资源版本始终定向到最新部署的容器版本。

```json
"hosting": {
  // ...

  // Add the "rewrites" attribute within "hosting"
  "rewrites": [ {
    "source": "..",      // path 路由，相当于nginx中的`location`配置项，在简单的反向代理场景下，应该配置为`**`，转发所有path的请求
    "run": {
      "serviceId": "helloworld",  // "service name" (from when you deployed the container image)
      "region": "us-central1",    // optional (if omitted, default is us-central1)
      "pinTag": true              // optional (see note below)
    }
  } ]
}
```

<a id="deploying"></a>
#### 部署
首先，理清 project 和 site 的关系，在 firebase 平台中创建响应的项目，当期项目中
   - project id 为 `supra-garage`
   - site id 为 `cloud-run-py`
 > 注意：
 > - firebase 平台站点可能有 bug，找不到创建 site 的入口，可以用 CLI 创建
 > - `$> firebase hosting:sites:create cloud-run-py

然后，配置工程文件`firebase.json`和`.firebaserc`，配置并引用 target

配置 target：
```.firebaserc
{
  "projects": {
    "default": "supra-garage"  // 配置项目 id
  },
  "targets": {
    "supra-garage": {
      "hosting": {
        "cloud-run-py": [     // target id
          "cloud-run-py"      // site id，注意一个target可以对应多个 site id，支持同时批量部署
        ]
      }
    }
  },
  "etags": {}
}
```

引用 target
```firebase.json
{
  "hosting": {
    "target": "cloud-run-py",      // 站点 id
    "public": "output/firebase/public",
    "ignore": [...],
    "rewrites": [{...}}]
  }
}
```

运行部署命令，`firebase deploy --only hosting:cloud-run-py`


## 一些说明

### `output/firebase/public` 目录说明

- **作用**：该目录用于 Firebase Hosting 的静态资源管理。当前可能为空，仅支持反向代理功能。
- **配置**：在 `firebase.json` 文件中通过以下配置指定：
  ```json
  {
    "hosting": {
      "public": "output/firebase/public"
    }
  }
  ```

### Firebase Hosting 部署说明

- **自动部署**：未启用 GitHub Actions 自动部署 Hosting。
- **理由**：Cloud Run 已通过 Cloud Build 实现自动部署，Hosting 配置变更较少，手动部署更灵活、可控。
- **手动部署**：更新 Hosting 配置时，运行 `firebase deploy --only hosting`。
- **注意**：手动部署可确保与 Cloud Run 部署的时序一致，避免潜在的配置不匹配问题。

### `.firebaserc` 文件配置说明

- **作用**：将本地项目与 Firebase 项目关联，允许 Firebase CLI 自动识别默认项目。
- **配置 google cloud project id**：替换文件包含默认项目 ID `supra-garage`。
- **开发者使用方法**：
    - 克隆项目后，可直接使用默认配置运行 Firebase CLI 命令。
    - 如需使用个人项目，运行 `firebase use --add` 添加并选择您的项目。

---
以下为原模板内容

# Cloud Run Template Microservice

A template repository for a Cloud Run microservice, written in Python

[![Run on Google Cloud](https://deploy.cloud.run/button.svg)](https://deploy.cloud.run)

## Prerequisite

* Enable the Cloud Run API via
  the [console](https://console.cloud.google.com/apis/library/run.googleapis.com?_ga=2.124941642.1555267850.1615248624-203055525.1615245957)
  or CLI:

```bash
gcloud services enable run.googleapis.com
```

## Features

* **Flask**: Web server framework
* **Buildpack support** Tooling to build production-ready container images from source code and without a Dockerfile
* **Dockerfile**: Container build instructions, if needed to replace buildpack for custom build
* **SIGTERM handler**: Catch termination signal for cleanup before Cloud Run stops the container
* **Service metadata**: Access service metadata, project ID and region, at runtime
* **Local development utilities**: Auto-restart with changes and prettify logs
* **Structured logging w/ Log Correlation** JSON formatted logger, parsable by Cloud Logging,
  with [automatic correlation of container logs to a request log](https://cloud.google.com/run/docs/logging#correlate-logs).
* **Unit and System tests**: Basic unit and system tests setup for the microservice
* **Task definition and execution**: Uses [invoke](http://www.pyinvoke.org/) to execute defined tasks in `tasks.py`.

## Local Development

### Cloud Code

This template works with [Cloud Code](https://cloud.google.com/code), an IDE extension
to let you rapidly iterate, debug, and run code on Kubernetes and Cloud Run.

Learn how to use Cloud Code for:

* Local
  development - [VSCode](https://cloud.google.com/code/docs/vscode/developing-a-cloud-run-service), [IntelliJ](https://cloud.google.com/code/docs/intellij/developing-a-cloud-run-service)

* Local
  debugging - [VSCode](https://cloud.google.com/code/docs/vscode/debugging-a-cloud-run-service), [IntelliJ](https://cloud.google.com/code/docs/intellij/debugging-a-cloud-run-service)

* Deploying a Cloud Run
  service - [VSCode](https://cloud.google.com/code/docs/vscode/deploying-a-cloud-run-service), [IntelliJ](https://cloud.google.com/code/docs/intellij/deploying-a-cloud-run-service)
* Creating a new application from a custom template (`.template/templates.json` allows for use as an app
  template) - [VSCode](https://cloud.google.com/code/docs/vscode/create-app-from-custom-template), [IntelliJ](https://cloud.google.com/code/docs/intellij/create-app-from-custom-template)

### CLI tooling

To run the `invoke` commands below, install [`invoke`](https://www.pyinvoke.org/index.html) system wide:

```bash
pip install invoke
```

Invoke will handle establishing local virtual environments, etc. Task definitions can be found in `tasks.py`.

#### Local development

1. Set Project Id:
    ```bash
    export GOOGLE_CLOUD_PROJECT=<GCP_PROJECT_ID>
    ```
2. Start the server with hot reload:
    ```bash
    invoke dev
    ```

#### Deploying a Cloud Run service

1. Set Project Id:
    ```bash
    export GOOGLE_CLOUD_PROJECT=<GCP_PROJECT_ID>
    ```

1. Enable the Artifact Registry API:
    ```bash
    gcloud services enable artifactregistry.googleapis.com
    ```

1. Create an Artifact Registry repo:
    ```bash
    export REPOSITORY="samples"
    export REGION=us-central1
    gcloud artifacts repositories create $REPOSITORY --location $REGION --repository-format "docker"
    ```

1. Use the gcloud credential helper to authorize Docker to push to your Artifact Registry:
    ```bash
    gcloud auth configure-docker
    ```

2. Build the container using a buildpack:
    ```bash
    invoke build
    ```
3. Deploy to Cloud Run:
    ```bash
    invoke deploy
    ```

### Run sample tests

1. [Pass credentials via `GOOGLE_APPLICATION_CREDENTIALS` env var](https://cloud.google.com/docs/authentication/production#passing_variable):
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="[PATH]"
    ```

2. Set Project Id:
    ```bash
    export GOOGLE_CLOUD_PROJECT=<GCP_PROJECT_ID>
    ```
3. Run unit tests
    ```bash
    invoke test
    ```

4. Run system tests
    ```bash
    gcloud builds submit \
        --config test/advance.cloudbuild.yaml \
        --substitutions 'COMMIT_SHA=manual,REPO_NAME=manual'
    ```
   The Cloud Build configuration file will build and deploy the containerized service
   to Cloud Run, run tests managed by pytest, then clean up testing resources. This configuration restricts public
   access to the test service. Therefore, service accounts need to have the permission to issue ID tokens for request
   authorization:
    * Enable Cloud Run, Cloud Build, Artifact Registry, and IAM APIs:
        ```bash
        gcloud services enable run.googleapis.com cloudbuild.googleapis.com iamcredentials.googleapis.com artifactregistry.googleapis.com
        ```

    * Set environment variables.
        ```bash
        export PROJECT_ID="$(gcloud config get-value project)"
        export PROJECT_NUMBER="$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')"
        ```

    * Create an Artifact Registry repo (or use another already created repo):
        ```bash
        export REPOSITORY="samples"
        export REGION=us-central1
        gcloud artifacts repositories create $REPOSITORY --location $REGION --repository-format "docker"
        ```

    * Create service account `token-creator` with `Service Account Token Creator` and `Cloud Run Invoker` roles.
        ```bash
        gcloud iam service-accounts create token-creator

        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:token-creator@$PROJECT_ID.iam.gserviceaccount.com" \
            --role="roles/iam.serviceAccountTokenCreator"
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:token-creator@$PROJECT_ID.iam.gserviceaccount.com" \
            --role="roles/run.invoker"
        ```

    * Add `Service Account Token Creator` role to the Cloud Build service account.
        ```bash
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
            --role="roles/iam.serviceAccountTokenCreator"
        ```

    * Cloud Build also requires permission to deploy Cloud Run services and administer artifacts:

        ```bash
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
            --role="roles/run.admin"
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
            --role="roles/iam.serviceAccountUser"
        gcloud projects add-iam-policy-binding $PROJECT_ID \
            --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
            --role="roles/artifactregistry.repoAdmin"
        ```

## Maintenance & Support

This repo performs basic periodic testing for maintenance. Please use the issue tracker for bug reports, features
requests and submitting pull requests.

## Contributions

Please see the [contributing guidelines](CONTRIBUTING.md)

## License
see: [LICENSE.md](LICENSE.md)
