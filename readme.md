# Azure IP Ranges Script

This script is a utility for retrieving and formatting the IP ranges of Microsoft Azure services. 
The original JSON file is downloaded from: https://www.microsoft.com/en-us/download/details.aspx?id=56519

## Last update

This repository contains the IPs from "ServiceTags_Public_20230522.json"

## Description

The script begins by downloading a JSON file from Microsoft's download page that contains the latest IP ranges for all Azure services. It then parses the JSON file to extract the unique system services and their associated IP addresses.

The IP addresses for each service are written to separate text files named after the service. These files are stored in the `ranges-services-pa` directory within the `output` directory. The format of these files is compatible with Palo Alto Networks (PA) devices.

## Disclaimer

This repository and its contents are provided "AS IS" without warranty of any kind, either express or implied, including, but not limited to, the implied warranties of merchantability, fitness for a particular purpose, or non-infringement. The creator and contributors to this repository are not responsible for any damages, including any general, special, incidental, or consequential damages, that may occur out of the use or inability to use these scripts or associated files.

## Recommendations

For organizations and individuals wishing to use the script in this repository, it is highly recommended to fork the repository. This is to ensure that you have control over any updates and can modify the script according to your specific needs.

The script parses a JSON file that Microsoft updates on a weekly basis. To ensure that you have the most recent IP address ranges, it is recommended that you download the new JSON file every week and perform the necessary changes at your site to correctly identify services running in Azure.

These service tags can also be used to simplify the Network Security Group rules for your Azure deployments though some service tags might not be available in all clouds and regions. For more information, please visit the [Azure Service Tags](http://aka.ms/servicetags) page.

## Contributions

Contributions to this project are welcome. Please feel free to submit a pull request or open an issue for discussion.

## License

This project is open-source and is licensed under the [MIT License](LICENSE).
