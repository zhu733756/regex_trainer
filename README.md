## regular_trainer
#### 项目功能：
 1 支持目标新闻网站文章正则rule生成，无需再编写crawlspier的rule逻辑;
 
 2 支持现有网站中大部分字段的文本密度提取器，无需再手写xpath，爬虫会自行总结
 
 3 文本密度提取逻辑参考[kingname/GeneralNewsExtractor](https://github.com/kingname/GeneralNewsExtractor);
 
 4 手动对批量link进行正则总结，可参考regex_trainer\tools\regex_collection.py
 ```
 t = RegexCollection("http://www.bjmy.gov.cn/", prefix=".*")
 t.add('http://www.bjmy.gov.cn/col/col129/index.html')
 t.add('http://www.bjmy.gov.cn/col/col3334/index.html')
 t.add('http://www.bjmy.gov.cn/art/2020/1/2/art_2052_6.html')
 t.add('http://www.bjmy.gov.cn/art/2020/1/2/art_2055_17.html')
 print(trie.extract())
 >>> [('.*/col/col\\d+/index.html', 3, 1, 2), ('.*/art/2020/1/2/art_205[_\\d]+.html', 5, 2, 2)]
 ```

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
 
```
CREATE TABLE `core_website_trainer_consumer` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `web_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `start_urls` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `job_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `allowed_domains` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `article_regex` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `created_at` datetime(6) DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(6),
  `updated_at` datetime(6) DEFAULT NULL,
  `status` int(11) DEFAULT NULL,
  `version` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `regex_trainer_task` (`web_name`,`job_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=116 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
```
```
CREATE TABLE `core_website_xpath_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `web_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL,
  `job_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci DEFAULT NULL,
  `version` int(11) NOT NULL,
  `sample` varchar(255) DEFAULT NULL,
  `sample_values` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `config` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `created_at` datetime(6) DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `web_version` (`web_name`,`job_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=92 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
```
#### 项目运行

1 pip install -r requirements.txt

2 进入 run.py 的目录, 修改命令行,修改自定义参数(-a 以及-s ),具体可参考scrapy命令行;
``` python
python run.py
```
也可以直接在项目子目录终端运行
```
scrapy crawl regex_trainer -a web_name=解放网 -a start_urls=https://www.jfdaily.com/home

```

