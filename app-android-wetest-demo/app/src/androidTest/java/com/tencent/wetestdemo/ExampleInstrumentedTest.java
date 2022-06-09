package com.tencent.wetestdemo;

import android.content.Context;

import androidx.lifecycle.Lifecycle;
import androidx.test.core.app.ActivityScenario;
import androidx.test.ext.junit.rules.ActivityScenarioRule;
import androidx.test.platform.app.InstrumentationRegistry;
import androidx.test.ext.junit.runners.AndroidJUnit4;

import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.runner.RunWith;

import static androidx.test.espresso.Espresso.onView;
import static androidx.test.espresso.action.ViewActions.click;
import static androidx.test.espresso.action.ViewActions.closeSoftKeyboard;
import static androidx.test.espresso.action.ViewActions.typeText;
import static androidx.test.espresso.assertion.ViewAssertions.matches;
import static androidx.test.espresso.matcher.ViewMatchers.isDisplayed;
import static androidx.test.espresso.matcher.ViewMatchers.withId;
import static androidx.test.espresso.matcher.ViewMatchers.withText;

/**
 * Instrumented test, which will execute on an Android device.
 *
 * @see <a href="http://d.android.com/tools/testing">Testing documentation</a>
 */
@RunWith(AndroidJUnit4.class)
public class ExampleInstrumentedTest {

    public void login(){
        onView(withId(R.id.username))
                .perform(typeText("wetest"), closeSoftKeyboard());
        onView(withId(R.id.password))
                .perform(typeText("wetest"), closeSoftKeyboard());
        onView(withId(R.id.login)).perform(click());
    }

    @Before
    public void launchActivity() {
        ActivityScenario<LoginActivity> scenario = ActivityScenario.launch(LoginActivity.class);
        scenario.moveToState(Lifecycle.State.RESUMED);
    }

    @Test
    public void useAppContext() {
        // Context of the app under test.
        Context appContext = InstrumentationRegistry.getInstrumentation().getTargetContext();
        org.junit.Assert.assertEquals("com.tencent.wetestdemo",
                appContext.getPackageName());
    }

    @Test
    public void runLoginSuccessTest()  {
        login();
        onView(withId(R.id.submitbtn)).check(matches(isDisplayed()));
    }

    @Test
    public void runLoginFailedTest()  {
        onView(withId(R.id.login)).perform(click());
        onView(withText("Login Failed")).check(matches(isDisplayed()));
    }

    @Test
    public void runSelectItemTest() {
        login();
        onView(withText("Item0")).perform(click());
        onView(withId(R.id.submitbtn)).perform(click());
        onView(withId(R.id.select_items)).check(matches(isDisplayed()));
    }

    @Test
    public void runFailedTest()  {
       assert false;
    }
}