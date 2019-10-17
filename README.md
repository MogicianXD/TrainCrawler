# TrainCrawler
从12306和火车票网爬取中国的火车站及车次信息，主要代码在crawl_12306.py的一部分和crawl_huochepiao.py

首先F12查看12306展开火车站时的响应文件，里面有个是调用api传来的json，url是https://www.12306.cn/index/script/core/common/station_name_v10036.js
v10036可能会随时间更新。

之后我是在https://download.csdn.net/download/weixin_44793842/11246303 这里找到了一份火车站与所属城市的对应表，不过格式不理想，稍做预处理。

然后get https://kyfw.12306.cn/otn/resources/js/query/train_list.js?scriptVersion=1.0 得到所有火车的列车号（该json记得是有不同版本的，选取第一个最新的读取）。

接着按照火车站爬取12306，但是12306的反爬机制很强，尽管我用fake_usragent库替换User-Agent，也爬取了西刺代理的ip建了个代理池（见get_ip.py），但效果很差，所以改爬火车票网了。
注：最近有找到一个不错的代理池，https://github.com/SpiderClub/haipproxy ，我爬知乎的时候很舒服，里面的检测代码可以自己修改成针对12306的

火车票网只需车次号就可以得到相应的列车信息表，不过有一些是过期的（没有对应的车站），我的项目不求准确性就都删除了。
要注意的一点是，火车票网的编码是gbk，尽管他的响应信息里好像是gb2313

之后的代码主要是为了入库做了很多的预处理，熟悉pandas就很简单

另外，我没有使用代理池，sleep5秒左右，爬一两天就可以全部爬完了

之前写的时候刚学python，可能代码不是很规范，还请见谅
