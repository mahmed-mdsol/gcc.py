
require 'ftools'

def take_screen_shot(file_name)
  driver = Capybara.current_session.driver
  if driver.class.name =~ /Vapir/i
    browser = driver.browser(:launch => false)
    browser.screen_capture(file_name) if browser
  elsif driver.browser.respond_to?(:save_screenshot)
    driver.browser.save_screenshot(File.expand_path(file_name))
  elsif page.driver.respond_to?(:render) #poltergeist
  	page.driver.render(file_name) rescue nil
  end
end

def when_or_then_step?(step)
  if step.respond_to?(:keyword)
  	["When","Then"].include?(step.keyword.strip) 
  else
    false
  end
end

output_dir = ENV['build_directory']

Before do |scenario|
  @step_count = 0
end

AfterStep do |scenario|
  scenario.source_tag_names.detect{|t| t =~ /@(PB.+)/} rescue nil # Get the @PB* tag
  pb = $1 || 'PB'
  dir = File.join(output_dir, pb)
  File.makedirs(dir) # make the directories if they don't already exist
  take_screen_shot(File.join(dir, "#{@step_count.to_i.to_s.rjust(5, '0')}.png"))# if when_or_then_step?(step)
  @step_count = @step_count.to_i + 1
end

