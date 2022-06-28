# hello-scheduler.rb

require 'sidekiq-scheduler'

class HelloWorld
  include Sidekiq::Worker

  def hello
    puts "Hii there "
  end
  def hello1
    puts " Hello after hello"
  end

  def perform
    hello
    hello1
    puts 'Hello world'
  end
end