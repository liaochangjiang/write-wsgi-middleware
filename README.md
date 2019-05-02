本文参考了：

- [https://github.com/alanctkc/wsgi-middleware-demo](https://github.com/alanctkc/wsgi-middleware-demo)
- [Youtube : Creating WSGI Middleware](https://www.youtube.com/watch?v=afnDANxsaYo)

[上篇文章](http://lcj.im/Python-Web%E5%BC%80%E5%8F%91%EF%BC%9A%E4%BB%8E-wsgi-%E5%BC%80%E5%A7%8B/)简要提到：wsgi 规范中的 app 是一个可调用对象，可以通过嵌套调用的方式实现中间件的功能。这篇文章就来亲自动手实现一下。

此文的重点在于 app 端，所以 wsgi 服务器将使用python 内置module `wsgiref.simple_server` 中的`make_server`。

# 创建 app

新建文件 `app.py` : 

```
def application(environ, start_response):
    """The web application."""
    
    response_body = ""
    for key, value in environ.items():
        response_body += "<p>{} : {}\n</p>".format(key, value)
        
    # Set up the response status and headers
    status = '200 OK'
    response_headers = [
        ('Content-Type', 'text/html; charset=utf-8'),
        ('Content-Length', str(len(response_body))),
    ]

    start_response(status, response_headers)
    return [response_body.encode('utf-8')]

```

> 注意：python3中要求 `response_body`是 bytes，所以需要 encode()一下。在 python2中是 str，不需要 encode()。

这个 app 做的事情非常简单，把传过来的 environ 原样返回。在开始返回body 之前，调用`server`传过来的`start_response`函数。

简要说明一下为什么是 `retuen [response_body]`而不是 `return response_body`或者 `return response_body.split("\n")`或者`return response_body.split("")`?

- 首先 wsgi 规范说明了`app`返回的是一个可迭代对象，列表是可迭代的。
- 其次，对于大多数 app 来说，response_body都不会太长，服务器的内存完成足以一次性装下，所以最高效的方法就是一次性把`response_body`全传过去。


# 创建 sever

新建文件`server.py`

```
from wsgiref.simple_server import make_server
from app import application

print("Server is running at http://localhost:8888 . Press Ctrl+C to stop.")
server = make_server('localhost', 8888, application)
server.serve_forever()

```

用浏览器打开 http://localhost:8888，就可以看到 environ 的详细内容。其中比较重要的我用红框框圈了起来。

![](http://lcjim-img.oss-cn-beijing.aliyuncs.com/2019-05-02-010658.png)

# 第一个中间件：cors

先**简要**了解一下 cors 的机制(详细的要比这个复杂点)：

如果一个ajax请求(XMLHttpRequest)是跨域的，比如说在 `http://localhost:9000`页面上向运行在`http://localhost:8888`的服务器发起请求，浏览器就会往请求头上面加上一个`ORIGIN`字段，这个字段的值就是`localhost:9000`。（对应在app 的 environ 参数中，就是 `HTTP_ORIGIN`）

同时，浏览器会先发出`OPTIONS`请求，服务器要实现这样的功能：如果想要接收这个请求的话，需要在response 的 headers里面添加一个`Access-Control-Allow-Origin`字段，值就是请求传过来的那个`ORIGIN`。

浏览器发出`OPTIONS`请求并发现返回数据的 headers 里面有`Access-Control-Allow-Origin`，才会进行下一步发出真正的请求：GET，POST，WAHTERVER。

所以，CORS 是浏览器和 Server共同协作来完成的。

看一下代码：

```
class CORSMiddleware(object):
    def __init__(self, app, whitelist=None):
        """Initialize the middleware for the specified app."""
        if whitelist is None:
            whitelist = []
        self.app = app
        self.whitelist = whitelist

    def validate_origin(self, origin):
        """Validate that the origin of the request is whitelisted."""
        return origin and origin in self.whitelist

    def cors_response_factory(self, origin, start_response):
        """Create a start_response method that includes a CORS header for the
        specified origin."""

        def cors_allowed_response(status, response_headers, exc_info=None):
            """This wraps the start_response behavior to add some headers."""
            response_headers.extend([('Access-Control-Allow-Origin', origin)])
            return start_response(status, response_headers, exc_info)

        return cors_allowed_response

    def cors_options_app(self, origin, environ, start_response):
        """A small wsgi app that responds to preflight requests for the
        specified origin."""
        response_body = 'ok'
        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(response_body))),
            ('Access-Control-Allow-Origin', origin),
            ('Access-Control-Allow-Headers', 'Content-Type'),
        ]
        start_response(status, response_headers)
        return [response_body.encode('utf-8')]

    def cors_reject_app(self, origin, environ, start_response):
        response_body = 'rejected'
        status = '200 OK'
        response_headers = [
            ('Content-Type', 'text/plain'),
            ('Content-Length', str(len(response_body))),
        ]
        start_response(status, response_headers)
        return [response_body.encode('utf-8')]

    def __call__(self, environ, start_response):
        """Handle an individual request."""
        origin = environ.get('HTTP_ORIGIN')
        if origin:
            if self.validate_origin(origin):
                method = environ.get('REQUEST_METHOD')
                if method == 'OPTIONS':
                    return self.cors_options_app(origin, environ, start_response)

                return self.app(
                    environ, self.cors_response_factory(origin, start_response))
            else:
                return self.cors_reject_app(origin, environ, start_response)

        else:
            return self.app(environ, start_response)

```

`__init__`方法传入的参数有：下一层的 app（回顾一下前面说的 app 是一层一层的，所以能够实现中间件）和 client 白名单，只允许来自这个白名单内的ajax 请求。

`__call__`方法说明这是一个可调用对象（类也可以是可调用的），一样接收两个参数：`environ`和`start_response`。首先判断一下 environ 中有没有`HTTP_ORIGIN`，有的话就表明属于跨域请求。如果是跨域，判断一下 origin 在不咋白名单。如果在白名单里面，如果是 `OPTIONS`请求，返回`cors_options_app`里面的对应内容（加上了`Access-Control-Allow-Origin` header）；如果不是`OPTIONS`请求，调用下一层的 app。如果不在白名单，返回的是`cors_reject_app`。

修改一下`server.py`:

```
app = CORSMiddleware(
    app=application,
    whitelist=[
        'http://localhost:9000',
        'http://localhost:9001'
    ]
)
server = make_server('localhost', 8000, app)
```

# 测试 cors app

这里在运行三个客户端，[代码在此]。(https://github.com/liaochangjiang/write-wsgi-middleware/)

运行`python client.py`：

![](http://lcjim-img.oss-cn-beijing.aliyuncs.com/2019-05-02-015355.png)

在浏览器打开`http://localhost:9000`、`http://localhost:9001`和`http://localhost:9002`，可以发现`http://localhost:9000`和`http://localhost:9001`成功发出了请求，而`http://localhost:9002`失败了。


![](http://lcjim-img.oss-cn-beijing.aliyuncs.com/2019-05-02-015553.png)

![](http://lcjim-img.oss-cn-beijing.aliyuncs.com/2019-05-02-015706.png)

# 第二个中间件：请求耗时

这个比上一个要简单很多，相信现在你已经完全能够理解了：

```
import time

class ResponseTimingMiddleware(object):
    """A wrapper around an app to print out the response time for each
    request."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        """Meaure the time spent in the application."""
        start_time = time.time()
        response = self.app(environ, start_response)
        response_time = (time.time() - start_time) * 1000
        timing_text = "总共耗时: {:.10f}ms \n".format(response_time)
        response = [timing_text.encode('utf-8') + response[0]]

        return response
```

再修改一下`server.py`：

```
app = ResponseTimingMiddleware(
    CORSMiddleware(
        app=application,
        whitelist=[
            'http://localhost:9000',
            'http://localhost:9001'
        ]
    )
)
```

再次访问`http://localhost:8000`，会看到最前面打印出了此次请求的耗时：

![](http://lcjim-img.oss-cn-beijing.aliyuncs.com/2019-05-02-020313.png)

# 总结一下

我手画了一个请求图，希望对你有所帮助：

![](http://lcjim-img.oss-cn-beijing.aliyuncs.com/2019-05-02-021150.png)

本文的所有源代码开源在 github 上：[https://github.com/liaochangjiang/write-wsgi-middleware](https://github.com/liaochangjiang/write-wsgi-middleware)

希望能点个 star ~
