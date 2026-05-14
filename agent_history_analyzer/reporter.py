"""报告生成模块"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from .constants import FlowItemType
from .models import AnalysisResult, FlowItem, RequestData
from .templates import (
    CSS_TEMPLATE,
    JS_TEMPLATE,
    escape_html,
    format_time_display,
    get_context_chart_section,
    get_header_section,
    get_html_body_end,
    get_html_body_start,
    get_html_end,
    get_html_head_end,
    get_html_start,
    get_metadata_section,
    get_stats_section,
    get_top_duration_section,
)


class HTMLReporter:
    """HTML报告生成器"""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._compression_index = 0
        self._flow_item_index = 0

    def generate(self, result: AnalysisResult, output_path: str) -> None:
        """生成HTML报告"""
        # 重置索引
        self._compression_index = 0
        self._flow_item_index = 0
        html_content = self._build_html(result)

        output_file = Path(output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"报告已生成: {output_file.absolute()}")

    def _build_html(self, result: AnalysisResult) -> str:
        """构建完整HTML"""
        parts = [
            get_html_start(),
            CSS_TEMPLATE,
            get_html_head_end(),
            get_html_body_start(),
            get_header_section(),
            get_stats_section(result.statistics),
            get_context_chart_section(result.compression_events),
            self._get_timeline_section(result.timeline),
            get_top_duration_section(result.top_duration_steps),
            get_metadata_section(
                str(self.file_path),
                result.total_events,
                result.statistics.total_time,
            ),
            get_html_body_end(),
            JS_TEMPLATE,
            get_html_end(),
        ]
        return "\n".join(parts)

    def _get_timeline_section(self, timeline: List[RequestData]) -> str:
        """生成时间线部分"""
        items = []
        for i, request in enumerate(timeline, 1):
            timestamp_str = datetime.fromtimestamp(request.start_time).strftime("%Y-%m-%d %H:%M:%S")
            details = self._generate_request_details(request)

            items.append(f"""<div class="timeline-item">
                <div class="request-header" onclick="toggleRequest(this)">
                    <div>
                        <span class="request-id">#{i} - {request.request_id}</span>
                        <span class="badge badge-blue">{timestamp_str}</span>
                        <span class="badge badge-green" style="margin-left: 10px;">总耗时: {request.duration:.2f}s</span>
                    </div>
                    <div>
                        <span class="arrow">▼</span>
                    </div>
                </div>
                <div class="request-details">
                    {details}
                </div>
            </div>""")

        items_joined = "\n".join(items)
        return f"""
        <div class="section">
            <h2 class="section-title">完整对话历史</h2>
            {items_joined}
        </div>"""

    def _generate_request_details(self, request: RequestData) -> str:
        """生成请求详情"""
        details = []

        if request.user_input:
            details.append(self._render_user_input(request.user_input))

        for flow_item in request.execution_flow:
            detail = self._render_flow_item(flow_item, request)
            if detail:
                details.append(detail)

        return "\n".join(details)

    def _render_user_input(self, user_input: str) -> str:
        """渲染用户输入"""
        index = self._flow_item_index
        self._flow_item_index += 1
        return f"""<div class="flow-item">
            <div class="message-box user-message" id="flow-item-{index}">
                <div class="message-header">
                    <span class="duration-badge">-</span>
                    <span class="badge badge-blue">用户输入</span>
                </div>
                <div class="message-content">{escape_html(user_input)}</div>
            </div>
        </div>"""

    def _render_flow_item(self, flow_item: FlowItem, request: RequestData) -> str:
        """渲染流程项"""
        if flow_item.type == FlowItemType.REASONING:
            return self._render_reasoning(flow_item)
        elif flow_item.type == FlowItemType.TOOL_CALL:
            return self._render_tool_call(flow_item)
        elif flow_item.type == FlowItemType.COMPRESSION:
            return self._render_compression(flow_item, request)
        elif flow_item.type == FlowItemType.ASSISTANT_RESPONSE:
            return self._render_assistant_response(flow_item)
        elif flow_item.type == FlowItemType.ASK_USER_QUESTION:
            return self._render_ask_user_question(flow_item)
        elif flow_item.type == FlowItemType.INVOCATION_PAUSED:
            return self._render_invocation_paused(flow_item)
        elif flow_item.type == FlowItemType.TASK_START:
            return self._render_task_start(flow_item)
        elif flow_item.type == FlowItemType.TASK_COMPLETE:
            return self._render_task_complete(flow_item)
        return ""

    def _render_reasoning(self, flow_item: FlowItem) -> str:
        """渲染推理过程"""
        index = self._flow_item_index
        self._flow_item_index += 1
        time_html = format_time_display(flow_item.duration)
        content = flow_item.content or ""

        return f"""<div class="flow-item">
            <div class="message-box assistant-message" id="flow-item-{index}">
                <div class="message-header">
                    {time_html}
                    <span class="badge badge-green">推理过程</span>
                </div>
                <div class="message-content">{escape_html(content)}</div>
            </div>
        </div>"""

    def _render_tool_call(self, flow_item: FlowItem) -> str:
        """渲染工具调用"""
        index = self._flow_item_index
        self._flow_item_index += 1
        tool_name = flow_item.name or "unknown"
        arguments = flow_item.arguments or "{}"
        timestamp_str = datetime.fromtimestamp(flow_item.timestamp).strftime("%H:%M:%S")
        time_html = format_time_display(flow_item.duration)
        params_html = self._format_tool_params(tool_name, arguments)

        result_html = ""
        if flow_item.result:
            result_html = f"""<div style="margin-top: 10px;">
                <div class="message-label"><strong>结果:</strong></div>
                <pre style="white-space: pre-wrap; word-wrap: break-word; background: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 0.85em;">{escape_html(str(flow_item.result))}</pre>
            </div>"""

        return f"""<div class="flow-item">
            <div class="message-box tool-call" id="flow-item-{index}">
                <div class="message-header">
                    {time_html}
                    <span class="badge badge-orange">工具调用: {tool_name}</span>
                    <span style="font-size: 0.9em; color: #999;">{timestamp_str}</span>
                </div>
                <div class="message-label"><strong>参数:</strong></div>
                {params_html}
                {result_html}
            </div>
        </div>"""

    def _render_compression(self, flow_item: FlowItem, request: RequestData) -> str:
        """渲染压缩事件"""
        timestamp_str = datetime.fromtimestamp(flow_item.timestamp).strftime("%H:%M:%S")

        prev_end_time = request.start_time
        for i, item in enumerate(request.execution_flow):
            if item == flow_item and i > 0:
                prev_item = request.execution_flow[i - 1]
                if prev_item.type == FlowItemType.TOOL_CALL:
                    prev_end_time = prev_item.timestamp + prev_item.duration
                elif prev_item.type == FlowItemType.REASONING:
                    prev_end_time = prev_item.end_timestamp or prev_item.timestamp
                elif prev_item.type == FlowItemType.ASSISTANT_RESPONSE:
                    prev_end_time = prev_item.end_timestamp or prev_item.timestamp
                elif prev_item.type == FlowItemType.ASK_USER_QUESTION:
                    prev_end_time = prev_item.timestamp
                elif prev_item.type == FlowItemType.INVOCATION_PAUSED:
                    prev_end_time = prev_item.timestamp
                elif prev_item.type == FlowItemType.TASK_START:
                    prev_end_time = prev_item.timestamp
                elif prev_item.type == FlowItemType.TASK_COMPLETE:
                    prev_end_time = prev_item.timestamp + prev_item.duration
                elif prev_item.type == FlowItemType.COMPRESSION:
                    prev_end_time = prev_item.timestamp
                break

        duration = flow_item.timestamp - prev_end_time
        time_html = format_time_display(duration)

        before = flow_item.before or 0
        after = flow_item.after or 0
        rate = flow_item.rate or 0
        compression_index = self._compression_index
        flow_index = self._flow_item_index
        self._compression_index += 1
        self._flow_item_index += 1

        return f"""<div class="flow-item">
            <div class="message-box compression" id="flow-item-{flow_index}" data-compression="{compression_index}">
                <div class="message-header">
                    {time_html}
                    <span class="badge badge-red">上下文压缩</span>
                    <span style="font-size: 0.9em; color: #999;">{timestamp_str}</span>
                </div>
                <div class="message-content">
                    <div>压缩前: {before} tokens</div>
                    <div>压缩后: {after} tokens</div>
                    <div>压缩率: {rate / 100:.1%}</div>
                </div>
            </div>
        </div>"""

    def _render_assistant_response(self, flow_item: FlowItem) -> str:
        """渲染助手响应"""
        index = self._flow_item_index
        self._flow_item_index += 1
        time_html = format_time_display(flow_item.duration)
        content = flow_item.content or ""

        return f"""<div class="flow-item">
            <div class="message-box assistant-message" id="flow-item-{index}">
                <div class="message-header">
                    {time_html}
                    <span class="badge badge-green">助手回复</span>
                </div>
                <div class="message-content">{escape_html(content)}</div>
            </div>
        </div>"""

    def _render_ask_user_question(self, flow_item: FlowItem) -> str:
        """渲染 chat.ask_user_question（权限审批、选项问卷等）"""
        index = self._flow_item_index
        self._flow_item_index += 1
        time_html = format_time_display(flow_item.duration)
        timestamp_str = datetime.fromtimestamp(flow_item.timestamp).strftime("%H:%M:%S")
        source = flow_item.source or ""
        source_badge = (
            f'<span class="badge badge-purple">{escape_html(source)}</span>' if source else ""
        )
        blocks_html = self._format_question_blocks(flow_item.questions or [])

        return f"""<div class="flow-item">
            <div class="message-box ask-user-question" id="flow-item-{index}">
                <div class="message-header">
                    {time_html}
                    <span class="badge badge-purple">向用户提问</span>
                    {source_badge}
                    <span style="font-size: 0.9em; color: #999;">{timestamp_str}</span>
                </div>
                {blocks_html}
            </div>
        </div>"""

    def _format_question_blocks(self, questions: List[Dict[str, Any]]) -> str:
        """将 questions 数组格式化为 HTML"""
        if not questions:
            summary = escape_html("(无 questions 字段)")
            return f'<div class="message-content">{summary}</div>'

        parts: List[str] = []
        for i, q in enumerate(questions, 1):
            header = q.get("header") or f"问题 {i}"
            body = q.get("question") or ""
            multi = q.get("multi_select")
            if multi is None:
                multi = q.get("multiSelect")
            mode = "多选" if multi else "单选"

            opts_lines: List[str] = []
            for opt in q.get("options") or []:
                if not isinstance(opt, dict):
                    continue
                label = opt.get("label") or ""
                desc = opt.get("description") or ""
                if desc:
                    opts_lines.append(f"<li><strong>{escape_html(label)}</strong> — {escape_html(desc)}</li>")
                else:
                    opts_lines.append(f"<li><strong>{escape_html(label)}</strong></li>")

            opts_html = (
                f"<ul class='question-options'>{''.join(opts_lines)}</ul>"
                if opts_lines
                else ""
            )

            parts.append(f"""<div class="question-block">
                <div class="message-label">{escape_html(header)} <span class="badge badge-blue">{mode}</span></div>
                <div class="message-content question-body">{escape_html(body)}</div>
                {opts_html}
            </div>""")

        return "\n".join(parts)

    def _render_invocation_paused(self, flow_item: FlowItem) -> str:
        """渲染 chat.invocation_paused（本轮调用暂停 / 流程中止点）"""
        index = self._flow_item_index
        self._flow_item_index += 1
        time_html = format_time_display(flow_item.duration)
        timestamp_str = datetime.fromtimestamp(flow_item.timestamp).strftime("%H:%M:%S")
        summary = escape_html(flow_item.content or "调用暂停")

        meta_lines: List[str] = []
        if flow_item.task_id:
            meta_lines.append(f"<div><span class='message-label'>任务 task_id：</span>{escape_html(flow_item.task_id)}</div>")
        if flow_item.awaiting_user_input is not None:
            label = "是" if flow_item.awaiting_user_input else "否"
            meta_lines.append(
                f"<div><span class='message-label'>等待用户输入 awaiting_user_input：</span>{label}</div>"
            )
        meta_html = "".join(meta_lines)

        note = (
            "<div class='message-content invocation-paused-note'>本轮 Agent 调用在此处结束；"
            "若上方为「等待用户输入」，通常需用户发送下一条消息后才会进入新的 request 继续执行。</div>"
        )

        return f"""<div class="flow-item">
            <div class="message-box invocation-paused" id="flow-item-{index}">
                <div class="message-header">
                    {time_html}
                    <span class="badge badge-amber">调用暂停</span>
                    <span style="font-size: 0.9em; color: #999;">{timestamp_str}</span>
                </div>
                <div class="message-label">摘要</div>
                <div class="message-content">{summary}</div>
                {meta_html}
                {note}
            </div>
        </div>"""

    def _render_task_start(self, flow_item: FlowItem) -> str:
        """渲染 task.start（Skill 阶段开始）"""
        index = self._flow_item_index
        self._flow_item_index += 1
        time_html = format_time_display(flow_item.duration)
        timestamp_str = datetime.fromtimestamp(flow_item.timestamp).strftime("%H:%M:%S")
        summary = escape_html(flow_item.content or "子任务开始")

        rows: List[str] = []
        if flow_item.task_id:
            rows.append(f"<div><span class='message-label'>task_id：</span>{escape_html(flow_item.task_id)}</div>")
        if flow_item.task_content:
            rows.append(f"<div><span class='message-label'>阶段：</span>{escape_html(flow_item.task_content)}</div>")
        if flow_item.task_index is not None and flow_item.total_tasks is not None:
            rows.append(
                f"<div><span class='message-label'>进度：</span>第 {flow_item.task_index + 1} / {flow_item.total_tasks} 步</div>"
            )
        if flow_item.parent_request_id:
            rows.append(
                f"<div><span class='message-label'>parent_request_id：</span>{escape_html(flow_item.parent_request_id)}</div>"
            )
        detail_html = "".join(rows)

        return f"""<div class="flow-item">
            <div class="message-box task-start" id="flow-item-{index}">
                <div class="message-header">
                    {time_html}
                    <span class="badge badge-teal">子任务开始</span>
                    <span style="font-size: 0.9em; color: #999;">{timestamp_str}</span>
                </div>
                <div class="message-label">摘要</div>
                <div class="message-content">{summary}</div>
                {detail_html}
            </div>
        </div>"""

    def _render_task_complete(self, flow_item: FlowItem) -> str:
        """渲染 task.complete（阶段结束与耗时）"""
        index = self._flow_item_index
        self._flow_item_index += 1
        time_html = format_time_display(flow_item.duration)
        timestamp_str = datetime.fromtimestamp(flow_item.timestamp).strftime("%H:%M:%S")
        summary = escape_html(flow_item.content or "子任务完成")

        status_badge = ""
        if flow_item.task_status:
            cls = "badge-green" if flow_item.task_status == "succeeded" else "badge-red"
            status_badge = f'<span class="badge {cls}">{escape_html(flow_item.task_status)}</span>'

        ms_line = ""
        if flow_item.task_duration_ms is not None:
            ms_line = f"<div><span class='message-label'>duration_ms：</span>{flow_item.task_duration_ms}</div>"

        err_html = ""
        if flow_item.task_error is not None:
            err_html = f"""<div style="margin-top: 8px;"><span class="message-label">error：</span>
                <pre style="white-space: pre-wrap; word-wrap: break-word; background: #ffebee; padding: 8px; border-radius: 4px; font-size: 0.85em;">{escape_html(str(flow_item.task_error))}</pre></div>"""

        return f"""<div class="flow-item">
            <div class="message-box task-complete" id="flow-item-{index}">
                <div class="message-header">
                    {time_html}
                    <span class="badge badge-cyan">子任务完成</span>
                    {status_badge}
                    <span style="font-size: 0.9em; color: #999;">{timestamp_str}</span>
                </div>
                <div class="message-label">摘要</div>
                <div class="message-content">{summary}</div>
                {ms_line}
                {err_html}
            </div>
        </div>"""

    def _format_tool_params(self, tool_name: str, arguments: str) -> str:
        """格式化工具参数"""
        try:
            params = json.loads(arguments)
        except (json.JSONDecodeError, TypeError):
            return f"<pre style='background: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 0.85em;'>{escape_html(arguments)}</pre>"

        if tool_name == "execute_python_code" and "code_block" in params:
            code = params["code_block"]
            return f"""<pre style="background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto; font-family: 'Courier New', monospace; font-size: 0.9em;"><code>{escape_html(code)}</code></pre>"""

        formatted_json = json.dumps(params, indent=2, ensure_ascii=False)
        return f"<pre style='background: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto; font-size: 0.85em;'>{escape_html(formatted_json)}</pre>"
