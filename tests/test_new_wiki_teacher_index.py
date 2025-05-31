
def test_new_wiki_teacher_index():
    from tnfsh_class_table.backend import NewWikiTeacherIndex
    wiki_index = NewWikiTeacherIndex.get_instance()
    wiki_index.export()



if __name__ == "__main__":
    test_new_wiki_teacher_index()
    print("NewWikiTeacherIndex test completed successfully.")