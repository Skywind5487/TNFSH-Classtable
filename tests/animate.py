"""課程調度的視覺化動畫
使用 networkx 和 matplotlib 來視覺化 DFS 搜尋過程
"""
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from model.node import TeacherNode, CourseNode
from model.utils import connect_neighbors
from typing import Dict, List, Set, Optional
import time

class AnimatedDFS:
    def __init__(self):
        # 創建圖形和布局
        self.G = nx.Graph()
        self.pos = None
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        
        # 追蹤搜索狀態
        self.visited: Set[CourseNode] = set()
        self.current_path: List[CourseNode] = []
        self.node_colors: Dict[CourseNode, str] = {}
        self.edge_colors: Dict[tuple, str] = {}
        
        # 動畫幀
        self.frames: List[dict] = []
        
    def setup_demo_graph(self):
        """建立示範圖"""
        # 建立教師節點
        A = TeacherNode('A')
        B = TeacherNode('B')
        C = TeacherNode('C')
        D = TeacherNode('D')
        
        # 建立課程節點
        a1 = CourseNode('1', A)
        a2 = CourseNode('2', A, is_free=True)
        b1 = CourseNode('1', B)
        b2 = CourseNode('2', B)
        c1 = CourseNode('1', C)
        c3 = CourseNode('3', C)
        d1 = CourseNode('1', D, is_free=True)
        d2 = CourseNode('2', D)
        
        # 建立連接
        connect_neighbors([a1, b2])
        connect_neighbors([b1, c3])
        connect_neighbors([c1, d2])
        
        # 加入圖形
        nodes = [a1, a2, b1, b2, c1, c3, d1, d2]
        self.G.add_nodes_from(nodes)
        
        # 加入邊
        for node in nodes:
            for neighbor in node.neighbors:
                self.G.add_edge(node, neighbor)
        
        # 設定節點位置
        self.pos = nx.spring_layout(self.G)
        
        # 初始化節點顏色
        self.node_colors = {node: 'lightblue' for node in self.G.nodes()}
        for node in nodes:
            if node.is_free:
                self.node_colors[node] = 'lightgreen'
        
        # 初始化邊顏色
        self.edge_colors = {edge: 'gray' for edge in self.G.edges()}
        
        return a1  # 返回起始節點

    def dfs_animate(self, start: CourseNode, max_depth: int = 5):
        """執行動畫化的 DFS"""
        def dfs(current: CourseNode, depth: int = 0):
            if depth >= max_depth:
                return
            
            # 更新當前節點狀態
            self.visited.add(current)
            self.current_path.append(current)
            self.node_colors[current] = 'red'  # 當前節點
            
            # 儲存當前幀
            self._save_frame(f"深度: {depth}\n訪問: {current}")
            
            # 遍歷相鄰節點
            for next_node in current.neighbors:
                if next_node not in self.visited:
                    # 標記正在考慮的邊
                    edge = tuple(sorted([current, next_node]))
                    self.edge_colors[edge] = 'red'
                    self._save_frame(f"深度: {depth}\n考慮: {current} -> {next_node}")
                    
                    # 遞迴搜索
                    dfs(next_node, depth + 1)
                    
                    # 回溯時重置邊的顏色
                    self.edge_colors[edge] = 'blue'
                    self._save_frame(f"深度: {depth}\n回溯: {next_node} -> {current}")
            
            # 回溯
            self.current_path.pop()
            if self.current_path:
                self.node_colors[current] = 'gray'  # 已訪問但不在當前路徑
            self._save_frame(f"深度: {depth}\n完成: {current}")
        
        # 開始 DFS
        dfs(start)
        
        # 創建動畫
        ani = animation.ArtistAnimation(
            self.fig, 
            self.frames,
            interval=1000,  # 每幀間隔1秒
            blit=True,
            repeat_delay=1000
        )
        
        # 顯示動畫
        plt.show()
    
    def _save_frame(self, title: str):
        """儲存當前圖形狀態為一幀"""
        # 清除之前的繪圖
        self.ax.clear()
        
        # 設定標題
        self.ax.set_title(title, pad=20)
        
        # 繪製邊
        for edge in self.G.edges():
            edge_key = tuple(sorted(edge))
            color = self.edge_colors.get(edge_key, 'gray')
            x1, y1 = self.pos[edge[0]]
            x2, y2 = self.pos[edge[1]]
            line = self.ax.plot([x1, x2], [y1, y2], color=color, zorder=1)[0]
        
        # 繪製節點
        for node in self.G.nodes():
            color = self.node_colors[node]
            x, y = self.pos[node]
            circle = plt.Circle((x, y), 0.1, color=color, zorder=2)
            self.ax.add_patch(circle)
            # 添加節點標籤
            self.ax.annotate(str(node), (x, y), 
                           xytext=(0, 0), textcoords='offset points',
                           ha='center', va='center')
        
        # 設定圖形範圍
        self.ax.set_xlim(-1.5, 1.5)
        self.ax.set_ylim(-1.5, 1.5)
        
        # 儲存當前幀
        self.frames.append([self.ax.patches[:] + self.ax.lines[:] + self.ax.texts[:]])

def main():
    # 創建動畫器
    animator = AnimatedDFS()
    
    # 設定示範圖並取得起始節點
    start_node = animator.setup_demo_graph()
    
    # 執行動畫化的 DFS
    animator.dfs_animate(start_node, max_depth=5)

if __name__ == "__main__":
    main()