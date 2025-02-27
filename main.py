#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
项目生成器：
- 在目录下新建Git项目或修改现有项目
- 使用OpenAI LLM流式输出内容
- 修改完成后自动进行Git提交
- OpenAI API密钥从.env文件读取，其他配置通过命令行参数指定
"""

import os
import sys
import argparse
import subprocess
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

import openai
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取OpenAI API密钥
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("错误：未找到OPENAI_API_KEY环境变量。请在.env文件中设置。")
    sys.exit(1)

openai.api_key = OPENAI_API_KEY


def create_or_modify_project(
    path: str, 
    project_type: str, 
    description: str, 
    files: List[str],
    commit_message: str,
    model: str = "gpt-4-turbo-preview"
) -> None:
    """
    创建或修改Git项目
    
    Args:
        path: 项目路径
        project_type: 项目类型（如python, nodejs等）
        description: 项目描述
        files: 要创建或修改的文件列表
        commit_message: Git提交信息
        model: 使用的OpenAI模型
    """
    project_path = Path(path).resolve()
    
    # 检查目录是否存在
    if not project_path.exists():
        print(f"创建项目目录: {project_path}")
        project_path.mkdir(parents=True, exist_ok=True)
        is_new_project = True
    else:
        is_new_project = False
        if not project_path.is_dir():
            print(f"错误：{project_path} 不是一个目录")
            return
    
    # 初始化Git仓库（如果是新项目或者目录不是Git仓库）
    if is_new_project or not (project_path / ".git").exists():
        print("初始化Git仓库...")
        subprocess.run(["git", "init"], cwd=project_path, check=True)
    
    # 为每个指定的文件生成或修改内容
    for file_path in files:
        full_path = project_path / file_path
        
        # 创建父目录（如果需要）
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取现有文件内容（如果存在）
        existing_content = ""
        if full_path.exists():
            with open(full_path, "r", encoding="utf-8") as f:
                existing_content = f.read()
        
        # 构建提示
        prompt = f"""
你的任务是为一个{project_type}项目{'创建' if not existing_content else '修改'}文件。

项目描述: {description}
文件路径: {file_path}

{"以下是现有文件内容，请在需要的地方进行修改:" if existing_content else "请生成适合该文件路径的内容:"}

{existing_content}
"""

        print(f"\n{'创建' if not existing_content else '修改'} {file_path} 中...")
        
        # 使用OpenAI API流式生成内容
        new_content = ""
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        
        for chunk in response:
            if "choices" in chunk and len(chunk["choices"]) > 0:
                content = chunk["choices"][0].get("delta", {}).get("content", "")
                if content:
                    print(content, end="", flush=True)
                    new_content += content
        
        # 写入生成的内容
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        print(f"\n{file_path} {'创建' if not existing_content else '修改'}完成")
    
    # 添加所有更改并提交
    print("\n添加文件到Git并提交...")
    subprocess.run(["git", "add", "."], cwd=project_path, check=True)
    subprocess.run(["git", "commit", "-m", commit_message], cwd=project_path, check=True)
    
    print(f"\n项目{('创建' if is_new_project else '修改')}完成并已提交到Git仓库!")


def main():
    """主函数，处理命令行参数并执行项目生成/修改"""
    parser = argparse.ArgumentParser(description="项目生成器 - 创建或修改Git项目")
    
    parser.add_argument("-p", "--path", required=True, help="项目路径")
    parser.add_argument("-t", "--type", required=True, help="项目类型（如python, nodejs等）")
    parser.add_argument("-d", "--description", required=True, help="项目描述")
    parser.add_argument("-f", "--files", nargs="+", required=True, help="要创建或修改的文件路径列表")
    parser.add_argument("-m", "--message", required=True, help="Git提交信息")
    parser.add_argument("--model", default="gpt-4-turbo-preview", help="使用的OpenAI模型")
    
    args = parser.parse_args()
    
    create_or_modify_project(
        path=args.path,
        project_type=args.type,
        description=args.description,
        files=args.files,
        commit_message=args.message,
        model=args.model
    )


if __name__ == "__main__":
    main()
