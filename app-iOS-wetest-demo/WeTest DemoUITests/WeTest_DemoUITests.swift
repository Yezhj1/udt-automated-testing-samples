//
//  WeTest_DemoUITests.swift
//  WeTest DemoUITests
//
//  Created by sergiotian on 2021/11/25.
//

import XCTest

class WeTest_DemoUITests: XCTestCase {

    override func setUpWithError() throws {
        // Put setup code here. This method is called before the invocation of each test method in the class.

        // In UI tests it is usually best to stop immediately when a failure occurs.
        continueAfterFailure = false

        // In UI tests it’s important to set the initial state - such as interface orientation - required for your tests before they run. The setUp method is a good place to do this.
    }

    override func tearDownWithError() throws {
        // Put teardown code here. This method is called after the invocation of each test method in the class.
    }
    
    func test_login_failed() throws{
        
        
        let app = XCUIApplication()
        app.launch()
        app/*@START_MENU_TOKEN@*/.staticTexts["Sign In"]/*[[".buttons[\"Sign In\"].staticTexts[\"Sign In\"]",".staticTexts[\"Sign In\"]"],[[[-1,1],[-1,0]]],[0]]@END_MENU_TOKEN@*/.tap()
        sleep(5)
        XCTAssertTrue(app.staticTexts["Login Failed"].exists)
        
    }

    func test_login_sucess() throws {
        // UI tests must launch the application that they test.
        let app = XCUIApplication()
        app.launch()
        let emailTextField = app.textFields["Email"]
        emailTextField.tap()
        emailTextField.typeText("wetest@wetest.net")
        let passwordTextField = app.secureTextFields["Password"]
        passwordTextField.tap()
        passwordTextField.typeText("123456")
        app/*@START_MENU_TOKEN@*/.staticTexts["Sign In"]/*[[".buttons[\"Sign In\"].staticTexts[\"Sign In\"]",".staticTexts[\"Sign In\"]"],[[[-1,1],[-1,0]]],[0]]@END_MENU_TOKEN@*/.tap()
        sleep(5)
        XCTAssertTrue(app.staticTexts["Submit"].exists)
    }
    
    func test_select_item_failed() throws{
        
        
        let app = XCUIApplication()
        app.launch()
        let emailTextField = app.textFields["Email"]
        emailTextField.tap()
        emailTextField.typeText("wetest@wetest.net")
        let passwordTextField = app.secureTextFields["Password"]
        passwordTextField.tap()
        passwordTextField.typeText("123456")
        app/*@START_MENU_TOKEN@*/.staticTexts["Sign In"]/*[[".buttons[\"Sign In\"].staticTexts[\"Sign In\"]",".staticTexts[\"Sign In\"]"],[[[-1,1],[-1,0]]],[0]]@END_MENU_TOKEN@*/.tap()
        sleep(5)
        app.staticTexts["Submit"].tap()
        XCTAssertTrue(app.staticTexts["Error"].exists)
        
    }
    
    func test_select_item_success() throws{
        let app = XCUIApplication()
        app.launch()
        let emailTextField = app.textFields["Email"]
        emailTextField.tap()
        emailTextField.typeText("wetest@wetest.net")
        let passwordTextField = app.secureTextFields["Password"]
        passwordTextField.tap()
        passwordTextField.typeText("123456")
        app/*@START_MENU_TOKEN@*/.staticTexts["Sign In"]/*[[".buttons[\"Sign In\"].staticTexts[\"Sign In\"]",".staticTexts[\"Sign In\"]"],[[[-1,1],[-1,0]]],[0]]@END_MENU_TOKEN@*/.tap()
        sleep(5)
        app.staticTexts["Item1"].tap()
        app.staticTexts["Item2"].tap()
        app.staticTexts["Item3"].tap()
        app.staticTexts["Submit"].tap()
        sleep(5)
        XCTAssertTrue(app.staticTexts["Order Detail"].exists)
    }

    func testLaunchPerformance() throws {
        if #available(macOS 10.15, iOS 13.0, tvOS 13.0, watchOS 7.0, *) {
            // This measures how long it takes to launch your application.
            measure(metrics: [XCTApplicationLaunchMetric()]) {
                XCUIApplication().launch()
            }
        }
    }
}
