# 启动前服务AS继承修订

2026-11-26 Asia/Shanghai，真实生成尚为0。静态复核发现：若模型服务从已硬限2GiB的driver直接fork，则服务也继承2GiB AS，无法保持既有模型服务配置及回滚基线语义。当前31项合同未实际启动Ollama，因此不能以其通过冒充此继承合同已测。

新增固定命令的service spawner，在driver降低AS之前启动；它只允许固定顺序16384/1024、各一次、已核SHA的既有Ollama binary，拒绝任意命令/模型/路径/次数，并只经有界本地pipe收发。该进程归入**service树16GiB监测预算**，与其Ollama子树一起计量；driver树扣除整个service树以免双计。driver及RPC/词表helper仍硬AS2GiB。服务保留原继承AS语义，未用driver额度限制服务，也没有提高容器24GiB或GPU16GiB监测阈值。

新增一个纯Python fixture真实子进程合同：服务spawner先继承256MiB，driver随后硬降64MiB，服务fixture子进程仍应256MiB；不启动Ollama、HTTP或模型。

工程登记次数由原自定2次调整为3次（增加此必要继承回归），**工程累计command上限仍240s、SSD16MiB/HDD32MiB不增加**；此前两次仅约4.14s。该调整属于用户“完成真实部署和验证”授权内必要工程修复，不新增真实请求或模型预算。所有旧通过/失败及source snapshot保留；修订后必须重新取得实际合同receipt，旧31项回执不放行改后代码。

两次真实生成/helper、156 HTTP、2000s真实阶段、128MiB HDD/32MiB SSD和160MiB完整回传上限均不变。新材料SHA及唯一授权在新合同通过后重新冻结；未通过不发真实请求。
