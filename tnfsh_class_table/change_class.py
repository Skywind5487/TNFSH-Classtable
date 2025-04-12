import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import rcParams
import math
import random as rand
from typing import List, Dict

# 設定中文字體
rcParams['font.sans-serif'] = ['Microsoft JhengHei']  # Windows系統中文顯示
rcParams['axes.unicode_minus'] = False  # 解決負號顯示問題

class CourseNode:
    def __init__(self, code: str):
        self.teacher: str = code[0].upper()  # 統一轉大寫
        self.time: int = int(code[1:])
        self.adjacency: List[str] = []
        self.is_free: bool = False
    
class TeacherNode:
    def __init__(self, name: str):
        self.children: List[str] = []
        self.name: str = name

# 全局變數
CourseNode_dict: Dict[str, CourseNode] = {}
TeacherNode_dict: Dict[str, TeacherNode] = {}

def connect_class(class_groups: List[List[str]]):
    """建立課程關係圖，輸入範例: [['a2', 'b3'], ['b2', 'd5']]"""
    for group in class_groups:
        # 確保所有課程節點存在
        for course in group:
            course_upper = course[0].upper() + course[1:]  # 統一格式
            if course_upper not in CourseNode_dict:
                CourseNode_dict[course_upper] = CourseNode(course_upper)
        
        # 建立雙向連接
        for i in range(len(group)):
            for j in range(i+1, len(group)):
                course1 = group[i][0].upper() + group[i][1:]
                course2 = group[j][0].upper() + group[j][1:]
                if course2 not in CourseNode_dict[course1].adjacency:
                    CourseNode_dict[course1].adjacency.append(course2)
                if course1 not in CourseNode_dict[course2].adjacency:
                    CourseNode_dict[course2].adjacency.append(course1)

def connect_teacher(teacher_name: str, course_code: str):
    """連接老師和課程，自動處理大小寫"""
    teacher_upper = teacher_name.upper()
    course_upper = course_code[0].upper() + course_code[1:]
    
    if teacher_upper not in TeacherNode_dict:
        TeacherNode_dict[teacher_upper] = TeacherNode(teacher_upper)
    if course_upper not in CourseNode_dict:
        CourseNode_dict[course_upper] = CourseNode(course_upper)
    # 連接老師到課程
    if course_upper not in TeacherNode_dict[teacher_upper].children:
        TeacherNode_dict[teacher_upper].children.append(course_upper)
    
    # 連接課程到老師
    CourseNode_dict[course_upper].father = teacher_upper

def search_course(course_code: str) -> List[List[str]]:
    """
    dfs搜索某個課程可調換的路徑

    Args:
        course_code: 課程代碼
        path: 已經走過的路徑
        max_depth: 最大搜索深度
        visited: 已訪問的課程集合

    Returns:
        List[List[str]]: 所有可能的調換路徑列表
    """
    all_paths = []
    path_stack = []
    visited = set()
    condition = True
    
    def dfs(max_depth):
        if len(path_stack) >= max_depth:
            if condition:
                all_paths.append(path_stack.copy())
            path_stack.pop()
            visited.remove(course_code)
            return
        
        if course_code in visited:
            return
        
        
        # 找同老師的其他課程
        teacher = CourseNode_dict[course_code].teacher
        for teacher_course in TeacherNode_dict[teacher].children:
            if teacher_course != course_code:
                visited.add(course_code)
                path_stack.append(course_code)
                dfs(teacher_course)
    dfs(course_code)
    return all_paths

def visualize_graph(save_path: str = None):
    """繪製並顯示或保存課程關係圖"""
    G = nx.Graph()
    teacher_colors = {
        'A': '#FF9999',  # 淺紅色
        'B': '#99CCFF',  # 淺藍色
        'C': '#88CC88',  # 墨綠色
        'D': '#CC99FF'   # 淺紫色
    }
    
    # 添加所有課程節點
    for course in CourseNode_dict.values():
        G.add_node(course.teacher + str(course.time), 
                  node_type='course', 
                  color=teacher_colors[course.teacher[0].upper()])
    
    # 添加所有老師節點
    for teacher in TeacherNode_dict.values():
        G.add_node(teacher.name, 
                  node_type='teacher', 
                  color=teacher_colors[teacher.name])
    
    # 添加所有邊
    for course in CourseNode_dict.values():
        # 課程與老師的邊
        G.add_edge(course.teacher + str(course.time), course.teacher[0].upper())
        
        # 課程之間的邊
        for adj_course in course.adjacency:
            G.add_edge(course.teacher + str(course.time), adj_course[0].upper() + adj_course[1:])
    
    # 繪圖設定
    plt.figure(figsize=(18, 14))
    
    # 多層次佈局 - 老師節點在外圈，課程節點在內圈
    pos = {}  # 初始化位置字典
    
    # 1. 老師節點位置 (外圈)
    teacher_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'teacher']
    radius = 15
    angle = 2 * math.pi / len(teacher_nodes)
    
    for i, node in enumerate(teacher_nodes):
        pos[node] = (radius * math.cos(i * angle), radius * math.sin(i * angle))
    
    # 2. 課程節點初始位置
    for course, node in CourseNode_dict.items():
        teacher_pos = pos[node.teacher[0].upper()]  # 直接使用大寫字母
        
        pos[course[0].upper() + course[1:]] = (teacher_pos[0] + rand.uniform(-4, 4), 
                      teacher_pos[1] + rand.uniform(-4, 4))
    
    # 3. 彈簧佈局優化
    pos = nx.spring_layout(G, pos=pos, fixed=teacher_nodes,
                         k=9.0,  # 大幅增加間距
                         iterations=300,  # 更多迭代
                         seed=42)
    
    # 分開繪製老師和課程節點
    teacher_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'teacher']
    course_nodes = [n for n, d in G.nodes(data=True) if d.get('node_type') == 'course']
    
    # 繪製老師節點（方形外框）
    nx.draw_networkx_nodes(G, pos, nodelist=teacher_nodes,
                         node_size=1800,
                         node_color=[d['color'] for n, d in G.nodes(data=True) 
                                    if d.get('node_type') == 'teacher'],
                         edgecolors='black',
                         linewidths=2.0,
                         node_shape='s')  # 方形
    
    # 繪製課程節點（圓形）
    nx.draw_networkx_nodes(G, pos, nodelist=course_nodes,
                         node_size=1200,
                         node_color=[d['color'] for n, d in G.nodes(data=True) 
                                    if d.get('node_type') == 'course'],
                         edgecolors='black',
                         linewidths=1.5)
    
    # 繪製所有連線
    edge_list = list(G.edges())
    nx.draw_networkx_edges(G, pos, edgelist=edge_list, width=2.0, edge_color='gray')
    
    # 繪製標籤
    labels = {n: d.get('label', n) for n, d in G.nodes(data=True)}
    nx.draw_networkx_labels(G, pos, labels, 
                          font_size=12, 
                          font_weight='bold',
                          font_family='Microsoft JhengHei')
    
    plt.title("課程關係圖\n(方形為老師，圓形為課程，同顏色為同老師)", 
             pad=20,
             fontproperties={'family':'Microsoft JhengHei', 'size':14})
    plt.axis('off')
    
    # 1. 標記d4為空堂
    CourseNode_dict['D4'].is_free = True

    # 2. 從b3搜索可調課路徑
    swap_paths = search_course('B3')

    # 3. 隨機選取一條路徑
    if swap_paths:
        selected_path = rand.choice(swap_paths)
        print(f"隨機選取的調課路徑: {selected_path}")
        
        # 在圖中標示選中路徑
        edge_list = [(selected_path[i], selected_path[i+1]) 
                    for i in range(len(selected_path)-1)
                    if selected_path[i] in G and selected_path[i+1] in G]
        
        if not edge_list:
            print(f"警告: 無效的調課路徑 - 路徑中的節點不存在於圖中: {selected_path}")
            return
        
        nx.draw_networkx_edges(G, pos, edgelist=edge_list, 
                             width=4.0, edge_color='red')
        
        # 標示起點和終點
        nx.draw_networkx_nodes(G, pos, nodelist=[selected_path[0]],
                             node_color='red', 
                             node_size=2000)
        nx.draw_networkx_nodes(G, pos, nodelist=[selected_path[-1]],
                             node_color='green',
                             node_size=2000)
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.show()


# 1. 定義班級分組
classes = [
    ['a2', 'b3', 'c1', 'd4'],
    ['b2', 'd5'],
    ['a3', 'c4'],
    ['a1', 'b5']
]

# 2. 建立課程關係
connect_class(classes)

# 3. 連接所有老師的課程 (A-D老師，1-5節課)
for teacher in ['A', 'B', 'C', 'D']:
    for time in range(1, 6):
        course = f"{teacher}{time}".lower()
        connect_teacher(teacher, course)

# 4. 繪製圖表 (可選保存)
visualize_graph(save_path="class_graph.png")