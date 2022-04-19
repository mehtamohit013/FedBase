# Arguments
*   Change the data path in monitor\_vehcile.py and ray\_power.py. Can replace them by a global config file.
*   Eliminate hardcoded path in process\_OSM.py
*   Update/ Recode the data path in dump.py
*   Correct torch.device everywhere

# Solution
*   Created a config.xml file and read it 
        from lxml import etree as et

        In [2]: et.parse('../config.xml')
        Out[2]: <lxml.etree._ElementTree at 0x7fa0416ffb40>

        In [3]: root = et.parse('../config.xml').getroot()

        In [4]: root.get('dpath')
        Out[4]: '/home/mohit/webots_code/release'
