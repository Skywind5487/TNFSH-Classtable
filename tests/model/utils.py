"""
提供共用的工具函式
"""
from typing import List, Dict, Set, Optional
from .node import CourseNode

def connect_neighbors(nodes: List[CourseNode]) -> None:
    """連接課程節點，使每個節點都成為其他節點的鄰居
    
    Args:
        nodes: 需要互相連接的課程節點列表
    """
    for course in nodes:
        course.neighbors = course.neighbors + [
            n for n in nodes 
            if (
                n is not course
                and not 
                n in course.neighbors
            )
        ]

def get_fwd(src: CourseNode, dst: CourseNode) -> Optional[CourseNode]:
    """取得前向課程節點
    
    Args:
        src: 源課程節點
        dst: 目標課程節點
    
    Returns:
        Optional[CourseNode]: 目標教師在源課程時間的課程，若不存在則返回 None
    """
    return dst.teacher.courses.get(src.time)

def get_bwd(src: CourseNode, dst: CourseNode) -> Optional[CourseNode]:
    """取得後向課程節點
    
    Args:
        src: 源課程節點
        dst: 目標課程節點
    
    Returns:
        Optional[CourseNode]: 源教師在目標課程時間的課程，若不存在則返回 None
    """
    return src.teacher.courses.get(dst.time)

def is_free(course: Optional[CourseNode], freed: Set[CourseNode]) -> bool:
    """檢查課程是否可用
    
    課程在以下情況被視為可用：
    1. 課程不存在（None）
    2. 課程標記為空堂（is_free=True）
    3. 課程已在當前路徑中被釋放（在 freed 集合中）
    
    Args:
        course: 要檢查的課程節點
        freed: 已被釋放的課程節點集合
        
    Returns:
        bool: 課程是否可用
    """
    return course is None or (course and course.is_free) or course in freed

def bwd_check(src: CourseNode, dst: CourseNode, *, freed: Set[CourseNode]) -> bool:
    """檢查後向移動是否合法
    
    Args:
        src: 源課程節點
        dst: 目標課程節點
        freed: 已釋放的課程節點集合
        
    Returns:
        bool: 後向移動是否合法
    """
    return is_free(get_bwd(src, dst), freed)

def fwd_check(src: CourseNode, dst: CourseNode, *, freed: Set[CourseNode]) -> bool:
    """檢查前向移動是否合法
    
    Args:
        src: 源課程節點
        dst: 目標課程節點
        freed: 已釋放的課程節點集合
        
    Returns:
        bool: 前向移動是否合法
    """
    return is_free(get_fwd(src, dst), freed)