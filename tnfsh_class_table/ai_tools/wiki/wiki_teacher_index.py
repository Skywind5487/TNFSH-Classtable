from tnfsh_class_table.utils.log_func import log_func

@log_func
def get_wiki_teacher_index() -> dict[str, dict[str, str]]:
    """
    從竹園Wiki索引資料，包括科目與老師名稱、其連結
    """
    from tnfsh_class_table.backend import NewWikiTeacherIndex
    index = NewWikiTeacherIndex.get_instance()
    return index.index