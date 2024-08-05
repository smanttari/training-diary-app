*** Settings ***
Documentation     Tests for trainings map functionalities.
Resource          ../resource.robot
Suite Setup       Setup Test Data And Log In
Suite Teardown    Remove Test Data And Close App


*** Test Cases ***
Filter By Date
    Given map page is opened
    When user sets startdate to "01.01.2020"
    And user sets enddate to "31.01.2020"
    Then training dropdown should contain "Kaikki"
    And training dropdown should contain "20200125-Skiing (free)-14.00km"
    And show button should be enabled

Filter By Sport
    Given map page is opened
    When user sets startdate to "01.01.2020"
    And user sets enddate to "31.01.2020"
    And user selects "Running"
    Then training dropdown should contain "----"
    And show button should be disabled

Filter By Sport Group
    Given map page is opened
    When user sets startdate to "01.01.2020"
    And user sets enddate to "31.01.2020"
    And user selects "Skiing"-group
    Then training dropdown should contain "Kaikki"
    And training dropdown should contain "20200125-Skiing (free)-14.00km"
    And show button should be enabled


*** Keywords ***
Setup Test Data And Log In
    Create Test User
    Open App
    Log Test User In    

Remove Test Data And Close App
    Log Out
    Delete Test User
    Close Browser

Map Page Is Opened
    Click Link      nav_trainings
    Click Link      nav_trainings_map

User Selects "${sport}"
    Select From List By Label       sport       ${SPACE*3}${sport}

User Selects "${sport}"-group
    Select From List By Label       sport       ${sport}

User Sets Startdate To "${date}"
    Input Text  startdate   ${date}  

User Sets Enddate To "${date}"
    Input Text  enddate   ${date}

Show Button Should Be Enabled
    Element Should Be Enabled      show

Show Button Should Be Disabled
    Element Should Be Disabled      show

Training Dropdown Should Contain "${training}"
    Set Selenium Implicit Wait      1 seconds
    ${trainings_list}        Get List Items     training
    List Should Contain Value       ${trainings_list}        ${training}