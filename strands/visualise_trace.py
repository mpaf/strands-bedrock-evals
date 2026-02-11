import json
from datetime import datetime

def ascii_trace(trace_file):
    with open(trace_file, 'r') as f:
        content = f.read()
    
    spans = []
    buffer = ""
    for line in content.split('\n'):
        buffer += line
        try:
            spans.append(json.loads(buffer))
            buffer = ""
        except json.JSONDecodeError:
            continue
    
    # Build hierarchy
    span_map = {s['context']['span_id']: s for s in spans}
    root = next(s for s in spans if s.get('parent_id') is None)
    
    def duration(span):
        start = datetime.fromisoformat(span['start_time'].replace('Z', '+00:00'))
        end = datetime.fromisoformat(span['end_time'].replace('Z', '+00:00'))
        return (end - start).total_seconds()
    
    print("\n" + "="*90)
    print("STRANDS AGENT EXECUTION TRACE")
    print("="*90)
    
    # Agent level
    attrs = root['attributes']
    print(f"\n┌─ 🤖 Agent: {attrs['gen_ai.agent.name']}")
    print(f"│  Model: {attrs['gen_ai.request.model'].split('.')[-1]}")
    print(f"│  Duration: {duration(root):.2f}s")
    print(f"│  Total Tokens: {attrs['gen_ai.usage.total_tokens']} (in:{attrs['gen_ai.usage.input_tokens']}, out:{attrs['gen_ai.usage.output_tokens']})")
    print(f"│  User: \"{root['events'][0]['attributes']['content'][:60]}...\"")
    
    # Cycles
    cycles = [s for s in spans if s['name'] == 'execute_event_loop_cycle']
    cycles.sort(key=lambda x: x['start_time'])
    
    for i, cycle in enumerate(cycles, 1):
        cycle_attrs = cycle['attributes']
        cycle_id = cycle_attrs['event_loop.cycle_id'][:8]
        parent_id = cycle_attrs.get('event_loop.parent_cycle_id', 'root')[:8]
        
        print(f"│")
        print(f"├─ 🔄 Cycle {i} [{cycle_id}]")
        print(f"│  │  Duration: {duration(cycle):.2f}s")
        if parent_id != 'root':
            print(f"│  │  Parent: {parent_id}")
        
        # Model invocations in this cycle
        chats = [s for s in spans if s['name'] == 'chat' and s.get('parent_id') == cycle['context']['span_id']]
        for chat in chats:
            chat_attrs = chat['attributes']
            print(f"│  │")
            print(f"│  ├─ 💬 Model Invoke")
            print(f"│  │  │  Duration: {duration(chat):.2f}s")
            print(f"│  │  │  Tokens: {chat_attrs['gen_ai.usage.total_tokens']}")
            
            # Check for tool use
            choice = next((e for e in chat['events'] if e['name'] == 'gen_ai.choice'), None)
            if choice and 'tool_use' in choice['attributes'].get('finish_reason', ''):
                print(f"│  │  │  Result: Tool calls requested")
        
        # Tools in this cycle
        tools = [s for s in spans if s['name'].startswith('execute_tool') and s.get('parent_id') == cycle['context']['span_id']]
        for tool in tools:
            tool_attrs = tool['attributes']
            print(f"│  │")
            print(f"│  ├─ 🔧 Tool: {tool_attrs['gen_ai.tool.name']}")
            print(f"│  │  │  Duration: {duration(tool):.2f}s")
            print(f"│  │  │  Status: {tool_attrs['gen_ai.tool.status']}")
    
    # Final response
    final = root['events'][-1]['attributes']['message'][:100]
    print(f"│")
    print(f"└─ ✅ Response: \"{final}...\"")
    print("\n" + "="*90 + "\n")

ascii_trace('strands/trace.out')
