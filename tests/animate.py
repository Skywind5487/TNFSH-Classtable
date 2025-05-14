"""Visualization of DFS search process in course scheduling
using networkx and matplotlib
"""
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import rcParams
import matplotlib.animation as animation
from model.node import TeacherNode, CourseNode
from model.utils import connect_neighbors, bwd_check, fwd_check
from typing import Dict, List, Set, Optional, Tuple
import time

# 設定中文字體
rcParams['font.family'] = ['Microsoft JhengHei UI', 'Arial Unicode MS']
rcParams['font.sans-serif'] = ['Microsoft JhengHei UI', 'Arial Unicode MS']
rcParams['axes.unicode_minus'] = False  # 解決負號顯示問題

# 顏色配置
COLOR_SCHEME = {
    'teacher': '#FFE4B5',     # 教師節點（米色）
    'current': 'red',         # 當前節點
    'free': 'lightgreen',     # 空堂
    'unvisited': 'lightblue', # 未訪問
    'visited': 'lightgray',   # 已訪問
    'path': 'yellow',         # 當前路徑
    'edge_normal': 'gray',    # 普通邊
    'edge_active': 'red',     # 活動邊
    'edge_invalid': 'orange'  # 無效邊
}

class AnimatedDFS:
    def __init__(self):
        # Create graph and layout
        self.G = nx.Graph()
        self.pos = None
        self.fig, self.ax = plt.subplots(figsize=(16, 12))
        
        # Track search state
        self.visited: Set[CourseNode] = set()
        self.current_path: List[CourseNode] = []
        self.node_colors: Dict[CourseNode, str] = {}
        self.edge_colors: Dict[tuple, str] = {}
        self.node_shapes: Dict[str, str] = {}  # 'circle' 或 'square'
        self.bwd_check_results: Dict[tuple, bool] = {}  # 存儲後向檢查結果
        
        # Animation frames
        self.frames: List[List] = []
        self.current_frame = 0
        
        # Set figure
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
        self.ax.axis('off')
        
        # Connect keyboard events
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)

    def on_key(self, event):
        if event.key == 'right':
            self.next_frame()
        elif event.key == 'left':
            self.prev_frame()
        elif event.key == 'r':
            self.reset_animation()
            
    def next_frame(self):
        if self.current_frame < len(self.frames) - 1:
            self.current_frame += 1
            self.update_display()
            
    def prev_frame(self):
        if self.current_frame > 0:
            self.current_frame -= 1
            self.update_display()
            
    def reset_animation(self):
        self.current_frame = 0
        self.update_display()

    def update_display(self):
        self.ax.clear()
        self.ax.set_xlim(-2, 2)
        self.ax.set_ylim(-2, 2)
        self.ax.axis('off')
        
        # Get current frame
        frame = self.frames[self.current_frame]
        nodes, edges, node_colors, edge_colors = frame
        
        # Draw edges with bwd check results
        for (i, j), color in zip(self.G.edges(), edge_colors):
            x1, y1 = self.pos[i]
            x2, y2 = self.pos[j]
            self.ax.plot([x1, x2], [y1, y2], color=color, linewidth=2, zorder=1)
              # 如果有後向檢查結果，顯示在邊上
            if (i, j) in self.bwd_check_results:
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                
                # 將檢查結果顯示在邊的上方
                offset = 0.1  # 標籤偏移量
                dx = x2 - x1
                dy = y2 - y1
                length = (dx**2 + dy**2)**0.5
                if length > 0:
                    norm_dx = -dy/length * offset  # 垂直於邊的向量
                    norm_dy = dx/length * offset
                else:
                    norm_dx = norm_dy = 0
                
                # 添加後向檢查結果標籤
                result = "可移動" if self.bwd_check_results[(i, j)] else "不可移動"
                color = "green" if self.bwd_check_results[(i, j)] else "red"
                self.ax.annotate(
                    result,
                    (mid_x + norm_dx, mid_y + norm_dy),
                    fontsize=8,
                    color=color,
                    bbox=dict(
                        boxstyle='round,pad=0.2',
                        fc='white',
                        ec=color,
                        alpha=0.9
                    ),
                    ha='center',
                    va='center',
                    fontfamily='Microsoft JhengHei UI'
                )
        
        # Draw nodes
        for node, color in zip(self.G.nodes(), node_colors):
            x, y = self.pos[node]
            
            # 根據節點類型選擇形狀
            if isinstance(node, TeacherNode):
                # 教師節點用方形
                rect = plt.Rectangle(
                    (x - 0.15, y - 0.15), 0.3, 0.3,
                    color=color, zorder=2
                )
                self.ax.add_patch(rect)
            else:
                # 課程節點用圓形
                circle = plt.Circle(
                    (x, y), 0.15,
                    color=color, zorder=2
                )
                self.ax.add_patch(circle)
            
            # Add node label with white background
            self.ax.annotate(
                str(node), (x, y),
                xytext=(0, 0),
                textcoords='offset points',
                ha='center',
                va='center',
                bbox=dict(
                    boxstyle='round,pad=0.5',
                    fc='white',
                    ec='none',
                    alpha=0.8
                ),
                fontsize=10
            )
          # Add frame info and legend
        self.ax.set_title(
            f'課表搜索步驟 {self.current_frame + 1}/{len(self.frames)}\n\n'
            '說明：方形=教師 圓形=課程 綠色=空堂',
            pad=20,
            fontfamily='Microsoft JhengHei UI'
        )
        
        # Add instructions
        self.fig.text(
            0.5, 0.02,
            '← →：上一步/下一步 | R：重置動畫 | Q：關閉',
            ha='center',
            fontfamily='Microsoft JhengHei UI'
        )
        
        plt.draw()

    def set_layout(self):
        # Use spring layout with optimized parameters
        self.pos = nx.spring_layout(
            self.G,
            k=1.5,  # 增加節點間的間距
            iterations=50,  # 增加迭代次數以獲得更好的布局
            seed=42  # 固定隨機種子以保持布局一致
        )
        
        # 調整布局以確保節點不會重疊
        self._adjust_node_positions()

    def _adjust_node_positions(self):
        """調整節點位置以避免重疊"""
        min_dist = 0.3  # 最小節點間距
        
        def get_dist(pos1, pos2):
            return ((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)**0.5
        
        # 迭代調整直到沒有重疊
        max_iterations = 50
        iteration = 0
        while iteration < max_iterations:
            overlaps = False
            
            # 檢查所有節點對
            nodes = list(self.G.nodes())
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    node1, node2 = nodes[i], nodes[j]
                    pos1, pos2 = self.pos[node1], self.pos[node2]
                    
                    dist = get_dist(pos1, pos2)
                    if dist < min_dist:
                        # 計算移動方向
                        dx = pos2[0] - pos1[0]
                        dy = pos2[1] - pos1[1]
                        if dist > 0:
                            dx /= dist
                            dy /= dist
                        else:  # 如果兩個節點完全重疊
                            dx, dy = 1, 0
                            
                        # 移動兩個節點
                        move = (min_dist - dist) / 2
                        self.pos[node1] = (pos1[0] - dx * move, pos1[1] - dy * move)
                        self.pos[node2] = (pos2[0] + dx * move, pos2[1] + dy * move)
                        overlaps = True
            
            if not overlaps:
                break
                
            iteration += 1
            
        # 確保所有節點都在視圖範圍內
        margin = 0.1
        for node in self.G.nodes():
            x, y = self.pos[node]
            x = max(-1.5 + margin, min(1.5 - margin, x))
            y = max(-1.5 + margin, min(1.5 - margin, y))
            self.pos[node] = (x, y)

    def setup_demo_graph(self):
        """Build a demo graph for testing
        
        路徑結構：
        Teacher A --- [A1] -> [B2] --- Teacher B
                  \         /
                   [A2_]  [B1_]
        
        說明：
        - A1 節需要移動
        - A2 是空堂，可以接收 A1（後向檢查）
        - B2 可以和 A1 交換
        - B1 是空堂，可以接收 B2（後向檢查）
        """
        # Create teacher nodes
        A = TeacherNode('A')
        B = TeacherNode('B')
        
        # Create course nodes
        a1 = CourseNode('1', A)  # 起點，需要交換
        a2 = CourseNode('2', A, is_free=True)  # 空堂，用於接收 A1
        b1 = CourseNode('1', B, is_free=True)  # 空堂，用於接收 B2
        b2 = CourseNode('2', B)  # 這節要交換
        
        # Create connections between courses
        connect_neighbors([a1, b2])
        
        # Add all nodes to graph (including teachers)
        nodes = [A, B, a1, a2, b1, b2]
        self.G.add_nodes_from(nodes)
        
        # Add edges between courses
        for node in [a1, a2, b1, b2]:
            for neighbor in node.neighbors:
                self.G.add_edge(node, neighbor)
        
        # Add edges between teachers and their courses
        self.G.add_edge(A, a1)
        self.G.add_edge(A, a2)
        self.G.add_edge(B, b1)
        self.G.add_edge(B, b2)
        
        # Set node positions using custom layout
        pos = {
            A: (-1.5, 0.5),   # 老師A在左上
            B: (1.5, 0.5),    # 老師B在右上
            a1: (-0.5, 0),    # A1在中間偏左
            b2: (0.5, 0),     # B2在中間偏右
            a2: (-1, -0.5),   # A2在左下
            b1: (1, -0.5),    # B1在右下
        }
        self.pos = pos
        
        # Initialize node colors
        self.node_colors = {node: 'lightblue' for node in self.G.nodes()}
        for node in [a1, a2, b1, b2]:
            if node.is_free:
                self.node_colors[node] = 'lightgreen'
        # 設定教師節點顏色
        self.node_colors[A] = '#FFE4B5'  # 米色
        self.node_colors[B] = '#FFE4B5'
        
        # Initialize edge colors
        self.edge_colors = {edge: 'gray' for edge in self.G.edges()}
        self.bwd_check_results = {}  # 清空後向檢查結果
        
        return a1  # Return start node

    def draw_static_frame(self, start: CourseNode):
        """Draw a static frame to test visualization
        
        Args:
            start: Start node to highlight
        """
        # Clear previous plot
        self.ax.clear()
        self.ax.axis('off')
        
        # Set title
        self.ax.set_title(
            f"DFS Search Demo\nStart node: {start}", 
            pad=20, fontsize=12
        )
        
        # Draw edges
        for edge in self.G.edges():
            color = self.edge_colors.get(edge, 'gray')
            x1, y1 = self.pos[edge[0]]
            x2, y2 = self.pos[edge[1]]
            self.ax.plot([x1, x2], [y1, y2], color=color, linewidth=2, zorder=1)
        
        # Draw nodes
        for node in self.G.nodes():
            color = 'red' if node == start else self.node_colors[node]
            x, y = self.pos[node]
            circle = plt.Circle((x, y), 0.15, color=color, zorder=2)
            self.ax.add_patch(circle)
            
            # Add node label with white background
            self.ax.annotate(
                str(node), (x, y),
                xytext=(0, 0),
                textcoords='offset points',
                ha='center',
                va='center',
                bbox=dict(
                    boxstyle='round,pad=0.5',
                    fc='white',
                    ec='none',
                    alpha=0.8
                ),
                fontsize=10
            )
        
        # Set figure title
        self.fig.suptitle(
            "DFS Search Visualization\n"
            "Red: Current node  Green: Free slot  Blue: Unvisited\n"
            "Press Space to pause/resume, Q to close", 
            fontsize=10, y=0.95
        )
        
        # Set figure limits
        self.ax.set_xlim(-1.5, 1.5)
        self.ax.set_ylim(-1.5, 1.5)
        
        # Show plot
        plt.show()

    def start_animation(self):
        # Set up keyboard event handling
        self.fig.canvas.mpl_connect('key_press_event', self.on_key)
        
        # Set initial frame
        self.current_frame = 0
        self.update_display()
        
        # Add title and instructions
        plt.title('DFS 課表搜索可視化\n← →: 上一步/下一步 | R: 重置', 
                 fontproperties='SimHei', pad=20)
        
        plt.show()

    def dfs_search(self, start: CourseNode):
        """執行 DFS 搜索並記錄每一步
        
        Args:
            start: 起始節點
        """
        self.visited.clear()
        self.current_path.clear()
        self._dfs_recursive(start)
        
    def _dfs_recursive(self, node: CourseNode):
        """遞迴執行 DFS 搜索
        
        Args:
            node: 當前節點
        """
        # 標記當前節點為已訪問
        self.visited.add(node)
        self.current_path.append(node)
        
        # 保存當前狀態
        self._save_frame(node)
        
        # 遍歷相鄰節點
        for neighbor in self.G.neighbors(node):
            # 跳過教師節點
            if isinstance(neighbor, TeacherNode):
                continue
                
            if neighbor not in self.visited:
                # 執行後向檢查
                is_valid = bwd_check(node, neighbor, freed=set())
                self.bwd_check_results[(node, neighbor)] = is_valid
                self.bwd_check_results[(neighbor, node)] = is_valid
                
                # 更新邊的顏色
                edge_color = 'red' if is_valid else 'orange'
                self.edge_colors[(node, neighbor)] = edge_color
                self.edge_colors[(neighbor, node)] = edge_color
                self._save_frame(node)
                
                if is_valid:
                    # 遞迴訪問
                    self._dfs_recursive(neighbor)
                
                # 回溯時將邊變為灰色
                self.edge_colors[(node, neighbor)] = 'gray'
                self.edge_colors[(neighbor, node)] = 'gray'
                
        # 回溯時移除當前節點
        self.current_path.pop()
        self._save_frame(node)
        
    def _save_frame(self, current_node: Optional[CourseNode] = None):
        """保存當前狀態作為新的幀
        
        Args:
            current_node: 當前正在訪問的節點
        """
        # 更新節點顏色
        node_colors = dict(self.node_colors)
        for node in self.G.nodes():
            if node == current_node:
                node_colors[node] = 'red'  # 當前節點
            elif node in self.current_path:
                node_colors[node] = 'yellow'  # 當前路徑
            elif node in self.visited:
                node_colors[node] = 'lightgray'  # 已訪問
            elif node.is_free:
                node_colors[node] = 'lightgreen'  # 空閒時段
            else:
                node_colors[node] = 'lightblue'  # 未訪問
        
        # 保存當前幀
        frame = [
            list(self.G.nodes()),
            list(self.G.edges()),
            [node_colors[n] for n in self.G.nodes()],
            [self.edge_colors.get(e, 'gray') for e in self.G.edges()]
        ]
        self.frames.append(frame)

def main():
    # 創建動畫器
    animator = AnimatedDFS()
    
    # 設置演示圖並獲取起始節點
    start_node = animator.setup_demo_graph()
    
    # 執行 DFS 搜索並記錄過程
    animator.dfs_search(start_node)
    
    # 開始動畫展示
    animator.start_animation()

if __name__ == "__main__":
    main()