Feature: seor suite metadata

  Scenario: The suite reports its member packages
    When I ask for the seor packages
    Then the core members are listed
