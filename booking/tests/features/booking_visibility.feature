Feature: Booking visibility and access control
  As a regular authenticated user
  I want to see only my own bookings in the list endpoint
  So that account data stays isolated between users

  Scenario: Regular user sees only their own bookings
    Given two users each have one booking
    And the first user is authenticated for the booking API
    When the first user requests the bookings list endpoint
    Then the booking list response status code is 200
    And only the first user's booking is returned
