//
//  WeTest_DemoTests.swift
//  WeTest DemoTests
//
//  Created by sergiotian on 2021/11/25.
//

import XCTest
@testable import WeTest_Demo

class WeTest_DemoTests: XCTestCase {

    override func setUpWithError() throws {
        // Put setup code here. This method is called before the invocation of each test method in the class.
    }

    override func tearDownWithError() throws {
        // Put teardown code here. This method is called after the invocation of each test method in the class.
    }
    
    func test_assert_int_success() throws {
        XCTAssert(123 == 123)
    }
    
    func test_assert_int_failed() throws {
        XCTAssert(123 == 1234)
    }

    func test_assert_string_success() throws {
        XCTAssertEqual("wetest","wetest")
        //var test1 = 2;
        
        // This is an example of a functional test case.
        // Use XCTAssert and related functions to verify your tests produce the correct results.
    }

    func testPerformanceExample() throws {
        // This is an example of a performance test case.
        self.measure {
            // Put the code you want to measure the time of here.
        }
    }

}
