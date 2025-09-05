# MCP ICP查询服务器 API文档

## 概述
本MCP服务器提供ICP备案信息查询功能，支持通过公司名称、ICP备案号或域名进行查询，并支持分页功能。

## 启动服务器
```bash
python server.py
```

## 工具接口

### query_icp
查询ICP备案信息，支持分页和多条件查询

#### 请求参数
| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| keyword | string | 是 | 查询关键词，可以是公司名称、ICP备案号或备案域名 |
| page | integer | 否 | 页码，默认为1 |

#### 响应参数
| 参数名 | 类型 | 描述 |
|-------|------|------|
| keyword | string | 查询关键词 |
| page | integer | 当前页码 |

##### data数组中每个对象的结构
| 参数名 | 类型 | 描述 |
|-------|------|------|
| domain | string | 备案域名 |
| contentTypeName | string | 内容类型名称 |
| domainId | integer | 域名ID |
| leaderName | string | 负责人姓名 |
| limitAccess | string | 是否限制访问 |
| mainId | integer | 主体ID |
| mainLicence | string | 主备案号 |
| natureName | string | 单位性质 |
| serviceId | integer | 服务ID |
| serviceLicence | string | 服务许可证号 |
| unitName | string | 单位名称 |
| updateRecordTime | string | 更新记录时间 |

#### 查询逻辑说明
当用户输入keyword时，系统将在以下字段中进行模糊匹配搜索：
- unitName (单位名称)
- mainLicence (主备案号)
- domain (备案域名)



#### 示例请求
```json
{
  "keyword": "北京百度网讯科技有限公司",
  "page": 1
}
```

#### 示例响应
```json
{
  "keyword": "北京百度网讯科技有限公司",
  "page": 1,
  "pageSize": 40,
  "total": 40,
  "records": [
    {
      "contentTypeName": "",
      "domain": "yjs-cdn3.com",
      "domainId": 10004879371,
      "leaderName": "",
      "limitAccess": "否",
      "mainId": 282751,
      "mainLicence": "京ICP证030173号",
      "natureName": "企业",
      "serviceId": 10001868696,
      "serviceLicence": "京ICP证030173号-102",
      "unitName": "北京百度网讯科技有限公司",
      "updateRecordTime": "2017-12-08 12:21:13"
    },
    {
      "contentTypeName": "",
      "domain": "sg.work",
      "domainId": 110005754296,
      "leaderName": "",
      "limitAccess": "否",
      "mainId": 282751,
      "mainLicence": "京ICP证030173号",
      "natureName": "企业",
      "serviceId": 110003776805,
      "serviceLicence": "京ICP证030173号-151",
      "unitName": "北京百度网讯科技有限公司",
      "updateRecordTime": "2021-12-10 10:18:46"
    },
    {
      "contentTypeName": "",
      "domain": "xiaoduzaijia.cn",
      "domainId": 10005613630,
      "leaderName": "",
      "limitAccess": "否",
      "mainId": 282751,
      "mainLicence": "京ICP证030173号",
      "natureName": "企业",
      "serviceId": 10002465207,
      "serviceLicence": "京ICP证030173号-155",
      "unitName": "北京百度网讯科技有限公司",
      "updateRecordTime": "2020-07-08 15:05:12"
    }
  ]
}
```