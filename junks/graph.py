import graphviz
import os

def draw_ast(node, dot=None):
    if dot is None:
        dot = graphviz.Digraph(comment='AST Tree')
        dot.attr('node', shape='box', style='filled, rounded', color='lightblue', fontname='Courier')

    node_id = str(id(node))
    
    # ラベルの作成
    label = type(node).__name__
    # 特定の属性を持っている場合にラベルに追加
    for attr in ['name', 'op', 'value']:
        if hasattr(node, attr):
            val = getattr(node, attr)
            label += f"\n{attr}: {val}"

    dot.node(node_id, label)

    # 子ノードを探索 (dataclassのフィールドを反復)
    # vars() や __dict__ を使って子要素を探す
    if hasattr(node, '__dict__'):
        for field_name, value in vars(node).items():
            if isinstance(value, list):
                for i, item in enumerate(value):
                    if hasattr(item, '__dict__') or isinstance(item, (int, str)): # 基本型かオブジェクト
                        child_id = draw_ast(item, dot)
                        dot.edge(node_id, child_id, label=f"{field_name}[{i}]")
            elif hasattr(value, '__dict__'):
                child_id = draw_ast(value, dot)
                dot.edge(node_id, child_id, label=field_name)
            elif field_name not in ['name', 'op', 'value']: # すでにラベルに書いたものは除外
                # プリミティブな値（数値や文字列）も葉ノードとして表示したい場合
                leaf_id = str(id(value)) + field_name
                dot.node(leaf_id, str(value), shape='ellipse', color='lightgrey')
                dot.edge(node_id, leaf_id, label=field_name)
            
    return node_id

# 実行部分
dot = graphviz.Digraph()

PARSE = """
[
<DEF_AST.Introductio object at 0x000002D61B06ABD0>, 
  FuncDecl(name='subjecto', body=[
    VarDecl(name='i', type_name='inte', expr=Num(value='1')), 
    RecurStmt(prima=Num(value='100'), propositio=Compare(op='<', left=Id(name='i'), right=Num(value='101')), gradu=GraduOpe(op='++', value=1), body=[
        IfStmt(cond=Compare(op='==', left=Binary(op='%', left=Id(name='i'), right=Num(value='15')), right=Num(value='0')), 
        then_body=[
            ExprStmt(expr=FlowCall(call=CallEmpty(name='indicant'), arg=Str(value='"FizzBuzz"')))
        ], 
        else_body=[
            IfStmt(cond=Compare(op='==', left=Binary(op='%', left=Id(name='i'), right=Num(value='3')), right=Num(value='0')), 
            then_body=[
                ExprStmt(expr=FlowCall(call=CallEmpty(name='indicant'), arg=Str(value='"Fizz"')))
            ], 
            else_body=[
                Through()
            ]),
            IfStmt(cond=Compare(op='==', left=Binary(op='%', left=Id(name='i'), right=Num(value='5')), right=Num(value='0')), then_body=[ExprStmt(expr=FlowCall(call=CallEmpty(name='indicant'), arg=Str(value='"Buzz"')))], else_body=[ExprStmt(expr=FlowCall(call=CallEmpty(name='indicant'), arg=Id(name='i')))])]), Assign(name='i', expr=Binary(op='+', left=Id(name='i'), right=Num(value='1'))), IfStmt(cond=Compare(op='>', left=Id(name='i'), right=Num(value='100')), then_body=[ExprStmt(expr=FlowCall(call=CallEmpty(name='indicant'), arg=Str(value='"limit over."'))), BreakStmt()], else_body=[Through()])])])]
"""
# PARSEがリストなので、中身を一つずつ描画
for element in PARSE:
    draw_ast(element, dot)

print(dot.source) # これを Edotor 等に貼り付け