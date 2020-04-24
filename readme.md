## regular_trainer
#### 项目功能：
 1 一个支持新闻网站逆向正则生成规则的scrapy项目
 2 支持现有网站中大部分字段的文本密度提取器，核心代码参考来源[kingname/GeneralNewsExtractor](https://github.com/kingname/GeneralNewsExtractor)

#### 项目启动配置
 1 修改setting.py
 ```
 MYSQL_HOST = '127.0.0.1'
 MYSQL_PORT = 3306
 MYSQL_DATABASE = '$news_crawler'
 MYSQL_USER = 'xxxx'
 MYSQL_PASSWORD = 'xxxx'
 ```

 2 数据库建表
 CREATE TABLE `core_website_xpath` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `web_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `version` int(11) NOT NULL,
  `config` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `updated_at` datetime(6) DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `web_version` (`web_name`,`version`) USING BTREE
 ) ENGINE=InnoDB AUTO_INCREMENT=75 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci 
 ROW_FORMAT=DYNAMIC;

 CREATE TABLE `core_website_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `web_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `start_urls` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `allowed_domains` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `article_regex` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `created_at` datetime(6) DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `web_name_regex` (`web_name`,`article_regex`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=76 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;

#### 项目运行
1 pip install -r requirements.txt
2 保证安装了scrapy运行环境以及tldextract(如果有其他包没安装,请pip install xxx)
3 进入 run.py 的目录, 修改命令行,修改自定义参数(-a 以及-s ),具体可参考scrapy命令行;
``` python
python run.py
```
也可以直接在项目子目录终端运行
scrapy crawl regex_trainer -a web_name=解放网 -a start_urls=https://www.jfdaily.com/home


