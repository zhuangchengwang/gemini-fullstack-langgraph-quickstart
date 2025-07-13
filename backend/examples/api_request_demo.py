"""
LangGraph HTTP请求参数传递演示

展示如何通过GET参数、POST参数、Headers等方式传递参数到LangGraph agent
"""

import asyncio
import httpx
import json
from typing import Dict, Any


class LangGraphAPIDemo:
    """LangGraph API 参数传递演示类"""
    
    def __init__(self, base_url: str = "http://localhost:2024", token: str = "user1-token"):
        self.base_url = base_url
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "LangGraph-Demo-Client/1.0",
            "X-Client-Version": "1.2.3",
            "X-Request-ID": "demo-request-123"
        }
    
    async def demo_query_params(self):
        """演示通过URL查询参数传递配置"""
        print("🔗 演示1: 通过URL查询参数传递配置")
        print("-" * 50)
        
        # 创建线程
        async with httpx.AsyncClient() as client:
            # 步骤1: 创建线程，通过查询参数传递配置
            create_url = f"{self.base_url}/threads"
            query_params = {
                # 自定义配置参数（会被提取到 custom_config 中）
                "config_language": "chinese",
                "config_search_region": "zh-CN",
                "config_max_results": "15",
                "config_search_depth": "detailed",
                "config_personalization_enabled": "true",
                
                # 直接参数（会被提取到 query_params 中）
                "search_type": "academic",
                "priority": "high",
                "timeout": "60",
                "lang": "zh",
                "region": "asia"
            }
            
            response = await client.post(
                create_url,
                headers=self.headers,
                params=query_params,
                json={"metadata": {"demo": "query_params"}}
            )
            
            if response.status_code == 200:
                thread_data = response.json()
                thread_id = thread_data["thread_id"]
                print(f"✅ 线程创建成功: {thread_id}")
                
                # 步骤2: 发送消息，继续使用查询参数
                run_url = f"{self.base_url}/threads/{thread_id}/runs"
                run_params = {
                    "stream": "true",
                    "config_response_format": "structured", 
                    "config_response_length": "detailed",
                    "config_include_sources": "true",
                    "search_focus": "technology",
                    "max_queries": "5"
                }
                
                run_data = {
                    "assistant_id": "agent",
                    "input": {
                        "messages": [
                            {"role": "user", "content": "人工智能的最新发展趋势"}
                        ]
                    }
                }
                
                response = await client.post(
                    run_url,
                    headers=self.headers,
                    params=run_params,
                    json=run_data
                )
                
                print(f"📤 发送请求: {run_url}")
                print(f"🔗 查询参数: {run_params}")
                print(f"📊 响应状态: {response.status_code}")
                
            else:
                print(f"❌ 请求失败: {response.status_code} - {response.text}")
    
    async def demo_headers(self):
        """演示通过请求头传递配置"""
        print("\n📋 演示2: 通过请求头传递配置")
        print("-" * 50)
        
        # 自定义请求头
        custom_headers = {
            **self.headers,
            # 自定义配置头（会被提取）
            "X-Language": "chinese",
            "X-Region": "china", 
            "X-Search-Type": "news",
            "X-Max-Results": "20",
            "X-Timezone": "Asia/Shanghai",
            "X-Client-Platform": "web",
            "X-Feature-Flags": "advanced_search,real_time"
        }
        
        async with httpx.AsyncClient() as client:
            # 创建线程
            response = await client.post(
                f"{self.base_url}/threads",
                headers=custom_headers,
                json={"metadata": {"demo": "headers"}}
            )
            
            if response.status_code == 200:
                thread_data = response.json()
                thread_id = thread_data["thread_id"]
                print(f"✅ 线程创建成功: {thread_id}")
                print(f"📋 使用的自定义头: {list(custom_headers.keys())}")
                
            else:
                print(f"❌ 请求失败: {response.status_code}")
    
    async def demo_post_body(self):
        """演示通过POST请求体传递配置"""
        print("\n📦 演示3: 通过POST请求体传递配置")
        print("-" * 50)
        
        async with httpx.AsyncClient() as client:
            # 创建线程
            response = await client.post(
                f"{self.base_url}/threads",
                headers=self.headers,
                json={"metadata": {"demo": "post_body"}}
            )
            
            if response.status_code == 200:
                thread_data = response.json()
                thread_id = thread_data["thread_id"]
                print(f"✅ 线程创建成功: {thread_id}")
                
                # 发送消息，通过请求体传递复杂配置
                run_data = {
                    "assistant_id": "agent",
                    "input": {
                        "messages": [
                            {"role": "user", "content": "区块链技术的应用前景"}
                        ],
                        # 直接在input中传递用户参数
                        "user_preferences": {
                            "language": "chinese",
                            "expertise_level": "intermediate",
                            "focus_areas": ["finance", "technology", "regulation"]
                        },
                        "search_config": {
                            "depth": "comprehensive",
                            "sources": ["academic", "news", "industry_reports"],
                            "time_range": "last_6_months"
                        }
                    },
                    "config": {
                        "configurable": {
                            # 通过config.configurable传递配置
                            "response_format": "detailed_analysis",
                            "include_charts": True,
                            "citation_style": "academic",
                            "language_preference": "chinese",
                            "search_region": "global",
                            "max_research_loops": 3,
                            "custom_instructions": "请重点关注中国市场的情况"
                        }
                    },
                    "metadata": {
                        "request_type": "research",
                        "priority": "high",
                        "user_context": {
                            "department": "research",
                            "project": "blockchain_analysis"
                        }
                    }
                }
                
                response = await client.post(
                    f"{self.base_url}/threads/{thread_id}/runs",
                    headers=self.headers,
                    json=run_data
                )
                
                print(f"📤 发送复杂配置请求")
                print(f"📊 响应状态: {response.status_code}")
                print(f"🎯 配置参数数量: {len(run_data['config']['configurable'])}")
                
            else:
                print(f"❌ 请求失败: {response.status_code}")
    
    async def demo_path_params(self):
        """演示路径参数的使用"""
        print("\n🛤️ 演示4: 路径参数的使用")
        print("-" * 50)
        
        async with httpx.AsyncClient() as client:
            # 创建线程
            response = await client.post(
                f"{self.base_url}/threads",
                headers=self.headers,
                json={"metadata": {"demo": "path_params"}}
            )
            
            if response.status_code == 200:
                thread_data = response.json()
                thread_id = thread_data["thread_id"]
                print(f"✅ 线程创建成功: {thread_id}")
                
                # 路径参数会被自动提取
                # /threads/{thread_id}/runs -> path_params = {"thread_id": "xxx"}
                print(f"🛤️ 路径中的thread_id将被自动提取: {thread_id}")
                
                # 创建run，run_id也会被提取
                response = await client.post(
                    f"{self.base_url}/threads/{thread_id}/runs",
                    headers=self.headers,
                    json={
                        "assistant_id": "agent",
                        "input": {"messages": [{"role": "user", "content": "Hello"}]}
                    }
                )
                
                if response.status_code == 200:
                    run_data = response.json()
                    run_id = run_data.get("run_id", "unknown")
                    print(f"🏃 Run创建成功: {run_id}")
                    print(f"🛤️ 路径参数将包含: thread_id={thread_id}, run_id={run_id}")
                
            else:
                print(f"❌ 请求失败: {response.status_code}")
    
    async def demo_combined_params(self):
        """演示组合使用多种参数传递方式"""
        print("\n🎭 演示5: 组合使用多种参数传递方式")
        print("-" * 50)
        
        # 组合所有参数传递方式
        query_params = {
            "config_priority": "urgent",
            "search_type": "comprehensive",
            "lang": "zh-CN"
        }
        
        custom_headers = {
            **self.headers,
            "X-Department": "AI-Research",
            "X-Project": "LangGraph-Demo",
            "X-Budget": "premium"
        }
        
        post_data = {
            "assistant_id": "agent",
            "input": {
                "messages": [
                    {"role": "user", "content": "人工智能在医疗领域的应用"}
                ],
                "context": {
                    "user_role": "researcher",
                    "domain": "healthcare"
                }
            },
            "config": {
                "configurable": {
                    "analysis_depth": "expert_level",
                    "include_case_studies": True,
                    "focus_regions": ["china", "usa", "eu"]
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            # 创建线程
            response = await client.post(
                f"{self.base_url}/threads",
                headers=custom_headers,
                params=query_params,
                json={"metadata": {"demo": "combined"}}
            )
            
            if response.status_code == 200:
                thread_data = response.json()
                thread_id = thread_data["thread_id"]
                print(f"✅ 线程创建成功: {thread_id}")
                
                # 发送消息，使用所有参数类型
                response = await client.post(
                    f"{self.base_url}/threads/{thread_id}/runs",
                    headers=custom_headers,
                    params=query_params,
                    json=post_data
                )
                
                print(f"📤 组合参数请求发送")
                print(f"🔗 查询参数: {query_params}")
                print(f"📋 自定义头: {[k for k in custom_headers.keys() if k.startswith('X-')]}")
                print(f"📦 POST配置: {post_data['config']['configurable']}")
                print(f"📊 响应状态: {response.status_code}")
                
            else:
                print(f"❌ 请求失败: {response.status_code}")


async def main():
    """主演示函数"""
    print("🚀 LangGraph HTTP请求参数传递完整演示")
    print("=" * 60)
    print("这个演示展示了如何通过各种HTTP方式传递参数到LangGraph agent")
    print()
    
    # 创建演示实例
    demo = LangGraphAPIDemo()
    
    try:
        # 演示各种参数传递方式
        await demo.demo_query_params()
        await demo.demo_headers()
        await demo.demo_post_body()
        await demo.demo_path_params()
        await demo.demo_combined_params()
        
        print("\n🎉 所有演示完成!")
        print("\n📝 总结:")
        print("1. URL查询参数: ?config_language=chinese&search_type=academic")
        print("2. 请求头: X-Language: chinese, X-Region: china")
        print("3. POST请求体: config.configurable 和 input 参数")
        print("4. 路径参数: /threads/{thread_id}/runs 自动提取")
        print("5. 组合方式: 同时使用多种参数传递方式")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        print("💡 请确保LangGraph服务正在运行，并且认证配置正确")


def show_parameter_mapping():
    """显示参数映射关系"""
    print("\n📊 参数映射关系说明")
    print("=" * 60)
    
    mapping_info = {
        "URL查询参数": {
            "格式": "?config_language=zh&search_type=news",
            "提取位置": "request_context.query_params",
            "特殊处理": "config_前缀的参数会提取到custom_config中",
            "示例": {
                "config_language": "custom_config.language",
                "search_type": "query_params.search_type"
            }
        },
        "请求头": {
            "格式": "X-Language: chinese",
            "提取位置": "request_context.headers",
            "特殊处理": "X-前缀的头会被特别处理",
            "过滤": "敏感头(Authorization, Cookie)会被过滤"
        },
        "POST请求体": {
            "格式": "config.configurable.* 和 input.*",
            "提取位置": "custom_config 和 body_params",
            "特殊处理": "config.configurable直接合并到custom_config"
        },
        "路径参数": {
            "格式": "/threads/{thread_id}/runs/{run_id}",
            "提取位置": "request_context.path_params",
            "自动提取": "URL模板中的{}参数自动提取"
        }
    }
    
    for param_type, info in mapping_info.items():
        print(f"\n{param_type}:")
        for key, value in info.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    print("🎯 LangGraph HTTP请求参数传递演示")
    print("这个演示需要LangGraph服务运行在 http://localhost:2024")
    print()
    
    # 显示参数映射说明
    show_parameter_mapping()
    
    # 运行演示（需要真实的LangGraph服务）
    print("\n🚀 开始API演示...")
    print("注意: 这需要LangGraph服务正在运行")
    # asyncio.run(main()) 