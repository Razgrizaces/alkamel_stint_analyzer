.get_attribute('id')
            result_elements = driver.find_element_by_id(results_id).find_elements_by_class_name("t")
            print(results_id)
            for i in range(0, len(result_elements)):
                csv_elements = (result_elements[i].find_elements_by_tag_name('a'))
                file_path = csv_elements[0].get_attribute('href')
                print(file_path)
                if '23_Analysis_Race' in file_path or '23_Analsysis_Race' in file_path:
                    if '.CSV' in file_path:
                        return file_path
            element = element - 1 